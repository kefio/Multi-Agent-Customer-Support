"""
Tools Module - Customer Support AI Tools for Swiss Airlines

This module provides a comprehensive set of tools for managing customer bookings
and inquiries across multiple domains: flights, hotels, car rentals, and excursions.
Each tool is implemented as a LangChain tool with proper error handling and validation.

The module includes:
- Policy lookup and company guidelines consultation
- Flight search, booking updates, and cancellations
- Hotel search, booking, and management
- Car rental search, booking, and management  
- Trip recommendations and excursion bookings
- Workflow delegation tools for specialized assistants

All tools interact with a SQLite database containing booking information
and enforce business rules for customer operations.
"""

import sqlite3
from datetime import datetime, date
from typing import Optional, Union
import numpy as np  # For numerical operations
from langchain_core.tools import tool  # For creating LangChain tools
import pytz  # For timezone handling
from langchain_core.runnables import RunnableConfig  # For runnable configuration
from customer_support_agent.policy_retriever import load_policy_retriever
from customer_support_agent.utils import local_file, backup_file, update_dates
from pydantic import BaseModel, Field

# Global policy retriever instance - initialized during setup
retriever = None


# === BASIC TOOLS ===

@tool
def lookup_policy(query: str) -> str:
    """
    Consult company policies to check whether certain options are permitted.
    
    This tool searches through Swiss Airlines' policy documents to provide
    guidance on what actions are allowed for customer requests. It should be
    used before making any flight changes or performing other sensitive operations.
    
    Args:
        query: Natural language query about company policies or specific scenarios
        
    Returns:
        Relevant policy information as formatted text
        
    Examples:
        >>> lookup_policy("Can I reschedule a flight within 3 hours of departure?")
        "Flight changes are not permitted within 3 hours of scheduled departure time..."
        
        >>> lookup_policy("What are the fees for hotel cancellations?")
        "Hotel cancellation policies vary by booking type..."
    """
    global retriever
    docs = retriever.query(query, k=2)
    return "\n\n".join([doc["page_content"] for doc in docs])


# === FLIGHT TOOLS ===

@tool
def fetch_user_flight_information(config: RunnableConfig) -> list[dict]:
    """
    Fetch comprehensive flight information for the authenticated user.

    Retrieves all tickets, flight details, and seat assignments for the current
    passenger. This includes booking references, flight schedules, airport codes,
    and seat allocations across all active bookings.

    Args:
        config: Runtime configuration containing passenger_id in configurable section

    Returns:
        List of dictionaries containing:
        - ticket_no: Unique ticket identifier
        - book_ref: Booking reference number
        - flight_id: Internal flight identifier
        - flight_no: Public flight number
        - departure_airport: IATA airport code for departure
        - arrival_airport: IATA airport code for arrival
        - scheduled_departure: Planned departure datetime
        - scheduled_arrival: Planned arrival datetime
        - seat_no: Assigned seat number
        - fare_conditions: Ticket class (economy, business, etc.)

    Raises:
        ValueError: If passenger_id is not provided in configuration
        
    Example:
        Returns data like:
        [
            {
                "ticket_no": "0005432000987",
                "book_ref": "00BFBB",
                "flight_id": 1185,
                "flight_no": "PG0134",
                "departure_airport": "DME",
                "arrival_airport": "BTK",
                "scheduled_departure": "2024-12-15 10:25:00+03:00",
                "scheduled_arrival": "2024-12-15 14:15:00+05:00",
                "seat_no": "2A",
                "fare_conditions": "Business"
            }
        ]
    """
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)
    if not passenger_id:
        raise ValueError("Passenger ID is required to fetch flight information.")
    
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()
    
    # Join tickets, flights, and boarding passes to get complete picture
    query = """
    SELECT 
        t.ticket_no, t.book_ref,
        f.flight_id, f.flight_no, f.departure_airport, f.arrival_airport, 
        f.scheduled_departure, f.scheduled_arrival,
        bp.seat_no, tf.fare_conditions
    FROM 
        tickets t
        JOIN ticket_flights tf ON t.ticket_no = tf.ticket_no
        JOIN flights f ON tf.flight_id = f.flight_id
        JOIN boarding_passes bp ON bp.ticket_no = t.ticket_no AND bp.flight_id = f.flight_id
    WHERE 
        t.passenger_id = ?
    """
    cursor.execute(query, (passenger_id,))
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results

@tool
def search_flights(
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Search for available flights based on specified criteria.
    
    Provides flexible flight search capabilities with optional filtering by
    airports, time ranges, and result limits. All parameters are optional
    to allow broad or specific searches based on customer needs.

    Args:
        departure_airport: IATA airport code for departure (e.g., "JFK", "LAX")
        arrival_airport: IATA airport code for arrival (e.g., "LHR", "CDG")
        start_time: Earliest departure time (ISO format: "2024-12-15 10:00:00")
        end_time: Latest departure time (ISO format: "2024-12-15 18:00:00")
        limit: Maximum number of results to return (default: 20)

    Returns:
        List of flight dictionaries containing:
        - flight_id: Unique flight identifier
        - flight_no: Public flight number (e.g., "LH123")
        - departure_airport: Origin airport code
        - arrival_airport: Destination airport code
        - scheduled_departure: Departure datetime
        - scheduled_arrival: Arrival datetime
        - aircraft_code: Aircraft type identifier
        - status: Flight status (Scheduled, Departed, Arrived, etc.)

    Examples:
        >>> search_flights(departure_airport="JFK", arrival_airport="LHR")
        [{"flight_id": 1234, "flight_no": "BA123", ...}]
        
        >>> search_flights(start_time="2024-12-15 10:00:00", limit=5)
        [{"flight_id": 5678, "flight_no": "LH456", ...}]
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    # Build dynamic query based on provided parameters
    query = "SELECT * FROM flights WHERE 1 = 1"
    params = []

    if departure_airport:
        query += " AND departure_airport = ?"
        params.append(departure_airport)

    if arrival_airport:
        query += " AND arrival_airport = ?"
        params.append(arrival_airport)

    if start_time:
        query += " AND scheduled_departure >= ?"
        params.append(start_time)

    if end_time:
        query += " AND scheduled_departure <= ?"
        params.append(end_time)
        
    query += " LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results

@tool
def update_ticket_to_new_flight(
    ticket_no: str, new_flight_id: int, *, config: RunnableConfig
) -> str:
    """
    Update the user's ticket to a new valid flight.
    
    This tool allows the AI to change the flight associated with a specific
    ticket number to a new, valid flight. It includes validation to ensure
    the new flight is not too close in time to the current time.

    Args:
        ticket_no (str): The unique identifier of the ticket to update.
        new_flight_id (int): The ID of the new flight to assign.
        config: Runtime configuration containing passenger_id.

    Returns:
        str: Success or error message.
        
    Raises:
        ValueError: If passenger_id is not provided in configuration.
        
    Example:
        >>> update_ticket_to_new_flight("0001234567890", 1234, config={"configurable": {"passenger_id": "12345"}})
        "Ticket successfully updated to new flight."
        
        >>> update_ticket_to_new_flight("0001234567890", 1234, config={"configurable": {"passenger_id": "12346"}})
        "Current signed-in passenger with ID 12346 not the owner of ticket 0001234567890"
    """
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)
    if not passenger_id:
        raise ValueError("No passenger ID configured.")

    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT departure_airport, arrival_airport, scheduled_departure FROM flights WHERE flight_id = ?",
        (new_flight_id,),
    )
    new_flight = cursor.fetchone()
    if not new_flight:
        cursor.close()
        conn.close()
        return "Invalid new flight ID provided."
    column_names = [column[0] for column in cursor.description]
    new_flight_dict = dict(zip(column_names, new_flight))
    timezone = pytz.timezone("Etc/GMT-3")
    current_time = datetime.now(tz=timezone)
    departure_time = datetime.strptime(
        new_flight_dict["scheduled_departure"], "%Y-%m-%d %H:%M:%S.%f%z"
    )
    time_until = (departure_time - current_time).total_seconds()
    if time_until < (3 * 3600):
        return f"Not permitted to reschedule to a flight that is less than 3 hours from the current time. Selected flight is at {departure_time}."

    cursor.execute(
        "SELECT flight_id FROM ticket_flights WHERE ticket_no = ?", (ticket_no,)
    )
    current_flight = cursor.fetchone()
    if not current_flight:
        cursor.close()
        conn.close()
        return "No existing ticket found for the given ticket number."

    # Check the signed-in user actually has this ticket
    cursor.execute(
        "SELECT * FROM tickets WHERE ticket_no = ? AND passenger_id = ?",
        (ticket_no, passenger_id),
    )
    current_ticket = cursor.fetchone()
    if not current_ticket:
        cursor.close()
        conn.close()
        return f"Current signed-in passenger with ID {passenger_id} not the owner of ticket {ticket_no}"

    # In a real application, you'd likely add additional checks here to enforce business logic,
    # like "does the new departure airport match the current ticket", etc.
    # While it's best to try to be *proactive* in 'type-hinting' policies to the LLM
    # it's inevitably going to get things wrong, so you **also** need to ensure your
    # API enforces valid behavior
    cursor.execute(
        "UPDATE ticket_flights SET flight_id = ? WHERE ticket_no = ?",
        (new_flight_id, ticket_no),
    )
    conn.commit()

    cursor.close()
    conn.close()
    return "Ticket successfully updated to new flight."

@tool
def cancel_ticket(ticket_no: str, *, config: RunnableConfig) -> str:
    """
    Cancel the user's ticket and remove it from the database.
    
    This tool allows the AI to remove a ticket from the system,
    which includes deleting the corresponding ticket_flights entry.

    Args:
        ticket_no (str): The unique identifier of the ticket to cancel.
        config: Runtime configuration containing passenger_id.

    Returns:
        str: Success or error message.
        
    Raises:
        ValueError: If passenger_id is not provided in configuration.
        
    Example:
        >>> cancel_ticket("0001234567890", config={"configurable": {"passenger_id": "12345"}})
        "Ticket successfully cancelled."
        
        >>> cancel_ticket("0001234567890", config={"configurable": {"passenger_id": "12346"}})
        "Current signed-in passenger with ID 12346 not the owner of ticket 0001234567890"
    """
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)
    if not passenger_id:
        raise ValueError("No passenger ID configured.")
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT flight_id FROM ticket_flights WHERE ticket_no = ?", (ticket_no,)
    )
    existing_ticket = cursor.fetchone()
    if not existing_ticket:
        cursor.close()
        conn.close()
        return "No existing ticket found for the given ticket number."

    # Check the signed-in user actually has this ticket
    cursor.execute(
        "SELECT ticket_no FROM tickets WHERE ticket_no = ? AND passenger_id = ?",
        (ticket_no, passenger_id),
    )
    current_ticket = cursor.fetchone()
    if not current_ticket:
        cursor.close()
        conn.close()
        return f"Current signed-in passenger with ID {passenger_id} not the owner of ticket {ticket_no}"

    cursor.execute("DELETE FROM ticket_flights WHERE ticket_no = ?", (ticket_no,))
    conn.commit()

    cursor.close()
    conn.close()
    return "Ticket successfully cancelled."   





# === HOTEL TOOLS ===

@tool
def search_hotels(
    location: Optional[str] = None,
    name: Optional[str] = None,
    price_tier: Optional[str] = None,
    checkin_date: Optional[Union[datetime, date]] = None,
    checkout_date: Optional[Union[datetime, date]] = None,
) -> list[dict]:
    """
    Search for available hotels based on specified criteria.
    
    Provides comprehensive hotel search functionality with flexible filtering
    options including location, hotel name, price tier, and date ranges.
    All parameters are optional to allow broad or targeted searches.

    Args:
        location: Geographic location or city name (e.g., "New York", "Paris")
        name: Specific hotel name or partial name for filtering
        price_tier: Hotel category/price level. Options include:
            - "Midscale": Budget-friendly options
            - "Upper Midscale": Mid-range comfort
            - "Upscale": Premium accommodations  
            - "Luxury": High-end luxury hotels
        checkin_date: Planned arrival date (datetime or date object)
        checkout_date: Planned departure date (datetime or date object)

    Returns:
        List of hotel dictionaries containing:
        - id: Unique hotel identifier
        - name: Hotel name
        - location: Hotel address/location
        - price_tier: Hotel category
        - rating: Hotel star rating or quality score
        - amenities: Available hotel features and services
        
    Examples:
        >>> search_hotels(location="Paris", price_tier="Upscale")
        [{"id": 123, "name": "Hotel Ritz Paris", "price_tier": "Luxury", ...}]
        
        >>> search_hotels(checkin_date=date(2024, 12, 15), checkout_date=date(2024, 12, 20))
        [{"id": 456, "name": "City Center Hotel", "location": "Downtown", ...}]
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    query = "SELECT * FROM hotels WHERE 1=1"
    params = []

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    # For the sake of this tutorial, we will let you match on any dates and price tier.
    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.close()

    return [
        dict(zip([column[0] for column in cursor.description], row)) for row in results
    ]

@tool
def book_hotel(hotel_id: int) -> str:
    """
    Book a hotel reservation using the hotel's unique identifier.
    
    Marks the specified hotel as booked in the system by updating its
    booking status. This is a simplified booking process for demo purposes.

    Args:
        hotel_id: Unique identifier of the hotel to book

    Returns:
        Success message if booking completed, error message if hotel not found
        
    Examples:
        >>> book_hotel(123)
        "Hotel 123 successfully booked."
        
        >>> book_hotel(999)
        "No hotel found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute("UPDATE hotels SET booked = 1 WHERE id = ?", (hotel_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully booked."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."

@tool
def update_hotel(
    hotel_id: int,
    checkin_date: Optional[Union[datetime, date]] = None,
    checkout_date: Optional[Union[datetime, date]] = None,
) -> str:
    """
    Update hotel reservation dates for an existing booking.
    
    Modifies the check-in and/or check-out dates for a hotel reservation.
    Either parameter can be updated independently or both can be changed together.

    Args:
        hotel_id: Unique identifier of the hotel reservation to update
        checkin_date: New check-in date (optional)
        checkout_date: New check-out date (optional)

    Returns:
        Success message if update completed, error message if hotel not found
        
    Examples:
        >>> update_hotel(123, checkin_date=date(2024, 12, 20))
        "Hotel 123 successfully updated."
        
        >>> update_hotel(999, checkout_date=date(2024, 12, 25))
        "No hotel found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    if checkin_date:
        cursor.execute(
            "UPDATE hotels SET checkin_date = ? WHERE id = ?", (checkin_date, hotel_id)
        )
    if checkout_date:
        cursor.execute(
            "UPDATE hotels SET checkout_date = ? WHERE id = ?",
            (checkout_date, hotel_id),
        )

    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully updated."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."

@tool
def cancel_hotel(hotel_id: int) -> str:
    """
    Cancel an existing hotel reservation.
    
    Removes the booking status from a hotel reservation, making it available
    for new bookings. This operation cannot be undone.

    Args:
        hotel_id: Unique identifier of the hotel reservation to cancel

    Returns:
        Success message if cancellation completed, error message if hotel not found
        
    Examples:
        >>> cancel_hotel(123)
        "Hotel 123 successfully cancelled."
        
        >>> cancel_hotel(999)  
        "No hotel found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute("UPDATE hotels SET booked = 0 WHERE id = ?", (hotel_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully cancelled."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."






# === CAR RENTAL TOOLS ===

@tool
def search_car_rentals(
    location: Optional[str] = None,
    name: Optional[str] = None,
    price_tier: Optional[str] = None,
    start_date: Optional[Union[datetime, date]] = None,
    end_date: Optional[Union[datetime, date]] = None,
) -> list[dict]:
    """
    Search for available car rental options based on specified criteria.
    
    Provides comprehensive car rental search functionality with flexible filtering
    by location, rental company, price tier, and rental period. All parameters
    are optional to support both broad searches and specific requirements.

    Args:
        location: Geographic location or city for car pickup (e.g., "Los Angeles", "London")
        name: Rental company name or partial name (e.g., "Hertz", "Avis", "Enterprise")
        price_tier: Vehicle category or price range (e.g., "Economy", "Compact", "Luxury")
        start_date: Rental start date (when customer picks up the car)
        end_date: Rental end date (when customer returns the car)

    Returns:
        List of car rental dictionaries containing:
        - id: Unique rental option identifier
        - name: Rental company name
        - location: Pickup/return location
        - vehicle_type: Car category (compact, SUV, luxury, etc.)
        - price_tier: Pricing category
        - daily_rate: Cost per day
        - availability: Current booking status
        
    Examples:
        >>> search_car_rentals(location="Miami", price_tier="Economy")
        [{"id": 234, "name": "Budget Car Rental", "vehicle_type": "Compact", ...}]
        
        >>> search_car_rentals(start_date=date(2024, 12, 15), end_date=date(2024, 12, 20))
        [{"id": 567, "name": "Enterprise", "location": "Airport", ...}]
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    query = "SELECT * FROM car_rentals WHERE 1=1"
    params = []

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    # For our tutorial, we will let you match on any dates and price tier.
    # (since our toy dataset doesn't have much data)
    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.close()

    return [
        dict(zip([column[0] for column in cursor.description], row)) for row in results
    ]

@tool
def book_car_rental(rental_id: int) -> str:
    """
    Book a car rental reservation using the rental option's unique identifier.
    
    Secures a car rental booking by marking the specified rental as booked
    in the system. This is a simplified booking process for demo purposes.

    Args:
        rental_id: Unique identifier of the car rental option to book

    Returns:
        Success message if booking completed, error message if rental not found
        
    Examples:
        >>> book_car_rental(234)
        "Car rental 234 successfully booked."
        
        >>> book_car_rental(999)
        "No car rental found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute("UPDATE car_rentals SET booked = 1 WHERE id = ?", (rental_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully booked."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."

@tool
def update_car_rental(
    rental_id: int,
    start_date: Optional[Union[datetime, date]] = None,
    end_date: Optional[Union[datetime, date]] = None,
) -> str:
    """
    Update rental dates for an existing car rental reservation.
    
    Modifies the pickup and/or return dates for a car rental booking.
    Either parameter can be updated independently or both can be changed together.

    Args:
        rental_id: Unique identifier of the car rental reservation to update
        start_date: New rental start date (when customer picks up the car)
        end_date: New rental end date (when customer returns the car)

    Returns:
        Success message if update completed, error message if rental not found
        
    Examples:
        >>> update_car_rental(234, start_date=date(2024, 12, 20))
        "Car rental 234 successfully updated."
        
        >>> update_car_rental(999, end_date=date(2024, 12, 25))
        "No car rental found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    if start_date:
        cursor.execute(
            "UPDATE car_rentals SET start_date = ? WHERE id = ?",
            (start_date, rental_id),
        )
    if end_date:
        cursor.execute(
            "UPDATE car_rentals SET end_date = ? WHERE id = ?", (end_date, rental_id)
        )

    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully updated."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."

@tool
def cancel_car_rental(rental_id: int) -> str:
    """
    Cancel an existing car rental reservation.
    
    Removes the booking status from a car rental reservation, making the
    vehicle available for new bookings. This operation cannot be undone.

    Args:
        rental_id: Unique identifier of the car rental reservation to cancel

    Returns:
        Success message if cancellation completed, error message if rental not found
        
    Examples:
        >>> cancel_car_rental(234)
        "Car rental 234 successfully cancelled."
        
        >>> cancel_car_rental(999)
        "No car rental found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute("UPDATE car_rentals SET booked = 0 WHERE id = ?", (rental_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully cancelled."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."


# === EXCURSION TOOLS ===

@tool
def search_trip_recommendations(
    location: Optional[str] = None,
    name: Optional[str] = None,
    keywords: Optional[str] = None,
) -> list[dict]:
    """
    Search for travel recommendations and excursion options based on specified criteria.
    
    Provides comprehensive search functionality for trip recommendations, tours,
    activities, and excursions. Supports flexible filtering by location, specific
    activity names, and keyword-based content matching.

    Args:
        location: Geographic location or destination (e.g., "Paris", "Tokyo", "Tuscany")
        name: Specific activity or tour name for targeted searches
        keywords: Comma-separated keywords describing desired activities
                 (e.g., "museum,art,culture" or "adventure,hiking,outdoor")

    Returns:
        List of trip recommendation dictionaries containing:
        - id: Unique recommendation identifier
        - name: Activity or excursion name
        - location: Geographic location or venue
        - description: Detailed activity description
        - keywords: Associated activity tags and categories
        - duration: Expected time commitment
        - price_range: Cost information
        - availability: Current booking status
        
    Examples:
        >>> search_trip_recommendations(location="Paris", keywords="museum,art")
        [{"id": 345, "name": "Louvre Museum Private Tour", "keywords": "museum,art,culture", ...}]
        
        >>> search_trip_recommendations(keywords="adventure,hiking")
        [{"id": 678, "name": "Mountain Trail Adventure", "location": "Alps", ...}]
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    query = "SELECT * FROM trip_recommendations WHERE 1=1"
    params = []

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    if keywords:
        keyword_list = keywords.split(",")
        keyword_conditions = " OR ".join(["keywords LIKE ?" for _ in keyword_list])
        query += f" AND ({keyword_conditions})"
        params.extend([f"%{keyword.strip()}%" for keyword in keyword_list])

    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.close()

    return [
        dict(zip([column[0] for column in cursor.description], row)) for row in results
    ]

@tool
def book_excursion(recommendation_id: int) -> str:
    """
    Book an excursion or trip recommendation using its unique identifier.
    
    Secures a booking for the specified trip recommendation, tour, or activity.
    This marks the excursion as booked in the system.

    Args:
        recommendation_id: Unique identifier of the trip recommendation to book

    Returns:
        Success message if booking completed, error message if recommendation not found
        
    Examples:
        >>> book_excursion(345)
        "Trip recommendation 345 successfully booked."
        
        >>> book_excursion(999)
        "No trip recommendation found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trip_recommendations SET booked = 1 WHERE id = ?", (recommendation_id,)
    )
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Trip recommendation {recommendation_id} successfully booked."
    else:
        conn.close()
        return f"No trip recommendation found with ID {recommendation_id}."

@tool
def update_excursion(recommendation_id: int, details: str) -> str:
    """
    Update details for an existing excursion or trip recommendation booking.
    
    Modifies the details or special requirements for a booked excursion.
    This could include time preferences, group size, accessibility needs, etc.

    Args:
        recommendation_id: Unique identifier of the trip recommendation to update
        details: New details or special requirements for the excursion

    Returns:
        Success message if update completed, error message if recommendation not found
        
    Examples:
        >>> update_excursion(345, "Wheelchair accessible tour requested")
        "Trip recommendation 345 successfully updated."
        
        >>> update_excursion(999, "Morning slot preferred")
        "No trip recommendation found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trip_recommendations SET details = ? WHERE id = ?",
        (details, recommendation_id),
    )
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Trip recommendation {recommendation_id} successfully updated."
    else:
        conn.close()
        return f"No trip recommendation found with ID {recommendation_id}."

@tool
def cancel_excursion(recommendation_id: int) -> str:
    """
    Cancel an existing excursion or trip recommendation booking.
    
    Removes the booking status from an excursion reservation, making it
    available for new bookings. This operation cannot be undone.

    Args:
        recommendation_id: Unique identifier of the trip recommendation to cancel

    Returns:
        Success message if cancellation completed, error message if recommendation not found
        
    Examples:
        >>> cancel_excursion(345)
        "Trip recommendation 345 successfully cancelled."
        
        >>> cancel_excursion(999)
        "No trip recommendation found with ID 999."
    """
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trip_recommendations SET booked = 0 WHERE id = ?", (recommendation_id,)
    )
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Trip recommendation {recommendation_id} successfully cancelled."
    else:
        conn.close()
        return f"No trip recommendation found with ID {recommendation_id}."




# === CONTROL FLOW ===

class CompleteOrEscalate(BaseModel):    
    """
    Control flow model for completing or escalating specialized assistant dialogs.
    
    Used by specialized assistants to signal when their task is complete
    or when they need to transfer control back to the primary assistant.
    This enables proper workflow transitions and prevents assistants from
    handling requests outside their domain expertise.
    
    Attributes:
        complete: Whether the current task is finished (default: True)
        reason: Explanation for why the dialog is being completed or escalated
    """
    complete: bool = True
    reason: str = Field(description="The reason for completing or escalating the dialog.")


# === ROUTING TOOLS ===
# Questi tool estendono la classe BaseModel e sono usati per istradare il controllo ad un altro sottografo
# Se trova una BaseModel senza funzione di esecuzione, costruisce internamente un “dummy tool” con:
# - nome = ToBookCarRental.__name__
# - schema JSON = schema Pydantic (campi + json_schema_extra)
# - callable che, quando viene invocato, restituisce l’istanza del modello (quindi nessuna “azione” reale).
# A runtime l’LLM, vedendo quello schema, può emettere una tool-call JSON del tipo:
# json
# Copia
# Modifica
# {
#   "name": "ToBookCarRental",
#   "arguments": {
#     "location": "Zurich",
#     "start_date": "2025-08-15",
#     "end_date": "2025-08-20",
#     "request": "compact automatic"
#   }
# }
# Questa chiamata non ha bisogno di “logica di business”: è un segnale di routing.



class ToFlightBookingAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle flight updates and cancellations."""

    request: str = Field(
        description="Any necessary followup questions the update flight assistant should clarify before proceeding."
    )

class ToBookCarRental(BaseModel):
    """Transfers work to a specialized assistant to handle car rental bookings."""

    location: str = Field(
        description="The location where the user wants to rent a car."
    )
    start_date: str = Field(description="The start date of the car rental.")
    end_date: str = Field(description="The end date of the car rental.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the car rental."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Basel",
                "start_date": "2023-07-01",
                "end_date": "2023-07-05",
                "request": "I need a compact car with automatic transmission.",
            }
        }

class ToHotelBookingAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle hotel bookings."""

    location: str = Field(
        description="The location where the user wants to book a hotel."
    )
    checkin_date: str = Field(description="The check-in date for the hotel.")
    checkout_date: str = Field(description="The check-out date for the hotel.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the hotel booking."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Zurich",
                "checkin_date": "2023-08-15",
                "checkout_date": "2023-08-20",
                "request": "I prefer a hotel near the city center with a room that has a view.",
            }
        }


class ToBookExcursion(BaseModel):
    """Transfers work to a specialized assistant to handle trip recommendation and other excursion bookings."""

    location: str = Field(
        description="The location where the user wants to book a recommended trip."
    )
    request: str = Field(
        description="Any additional information or requests from the user regarding the trip recommendation."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Lucerne",
                "request": "The user is interested in outdoor activities and scenic views.",
            }
        }
