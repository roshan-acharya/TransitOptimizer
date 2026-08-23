import random
from dataclasses import dataclass



ZONES = [
    "Gongabu",
    "Balaju",
    "Kalanki",
    "Balkumari",
    "Satdobato",
    "Koteshwor",
    "Tinkune",
    "Chabahil",
]


# ============================================================
# SIMULATION PARAMETERS
# ============================================================

STEP_MINUTES = 5

BUS_CAPACITY = 30

TOTAL_FLEET = 20

FARE_PER_PASSENGER = 30

COST_PER_STEP = 40


# Base passenger arrivals per 5-minute step
BASE_DEMAND = {
    "Gongabu": 10,
    "Balaju": 7,
    "Kalanki": 12,
    "Balkumari": 8,
    "Satdobato": 9,
    "Koteshwor": 14,
    "Tinkune": 8,
    "Chabahil": 10,
}


# ============================================================
# BUS
# ============================================================

@dataclass
class Bus:

    bus_id: int

    # Position in the Ring Road
    position: int = 0

    # Current passengers
    passengers: int = 0

    # Is bus currently making a Ring Road trip?
    active: bool = False

    # Statistics
    trips_completed: int = 0

    total_passengers_served: int = 0

    revenue: float = 0.0

    operating_cost: float = 0.0


    # --------------------------------------------------------
    # Current zone
    # --------------------------------------------------------

    @property
    def zone(self):

        return ZONES[self.position]


    # --------------------------------------------------------
    # Occupancy
    # --------------------------------------------------------

    @property
    def occupancy(self):

        return self.passengers / BUS_CAPACITY


    # --------------------------------------------------------
    # Reset bus
    # --------------------------------------------------------

    def reset(self):

        self.position = 0

        self.passengers = 0

        self.active = False

        self.trips_completed = 0

        self.total_passengers_served = 0

        self.revenue = 0.0

        self.operating_cost = 0.0


# ============================================================
# RING ROAD ENVIRONMENT
# ============================================================

class RingRoadEnvironment:

    def __init__(self):

        self.zones = ZONES

        self.buses = [
            Bus(bus_id=i + 1)
            for i in range(TOTAL_FLEET)
        ]

        self.reset()


    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        # Simulation time
        self.time = 0

        # Last time a bus was dispatched
        self.last_dispatch_time = 0

        # ----------------------------------------------------
        # Passenger queues
        # ----------------------------------------------------

        self.waiting = {
            zone: 0
            for zone in self.zones
        }

        # ----------------------------------------------------
        # Total passenger waiting time
        #
        # Unit:
        # passenger-minutes
        # ----------------------------------------------------

        self.waiting_time = {
            zone: 0
            for zone in self.zones
        }

        # ----------------------------------------------------
        # Global statistics
        # ----------------------------------------------------

        self.total_arrivals = 0

        self.total_served = 0

        self.total_revenue = 0.0

        self.total_cost = 0.0

        self.total_profit = 0.0

        self.completed_trips = 0

        # ----------------------------------------------------
        # Reset fleet
        # ----------------------------------------------------

        for bus in self.buses:

            bus.reset()

        return self.get_state()


    # ========================================================
    # CURRENT SIMULATION TIME
    # ========================================================

    def current_hour(self):

        minutes = self.time * STEP_MINUTES

        return 6 + minutes / 60


    # ========================================================
    # DEMAND MULTIPLIER
    # ========================================================

    def demand_multiplier(self):

        hour = self.current_hour()

        # Morning peak
        if 7 <= hour < 9:

            return 1.8

        # Evening peak
        if 16 <= hour < 19:

            return 1.8

        # Midday lower demand
        if 10 <= hour < 15:

            return 0.8

        # Normal demand
        return 1.0


    # ========================================================
    # GENERATE PASSENGERS
    # ========================================================

    def generate_passengers(self):

        multiplier = self.demand_multiplier()

        arrivals_this_step = {}

        for zone in self.zones:

            expected = (
                BASE_DEMAND[zone]
                * multiplier
            )

            # Random demand around expected value
            arrivals = max(
                0,
                round(
                    random.gauss(
                        expected,
                        expected * 0.20
                    )
                )
            )

            self.waiting[zone] += arrivals

            self.total_arrivals += arrivals

            arrivals_this_step[zone] = arrivals

        return arrivals_this_step


    # ========================================================
    # DISPATCH BUS FROM GONGABU
    # ========================================================

    def dispatch_bus(self):

        # Find a bus that is currently available
        for bus in self.buses:

            if not bus.active:

                # Bus starts from Gongabu
                bus.position = 0

                bus.passengers = 0

                bus.active = True

                return bus.bus_id

        # No bus available
        return None


    # ========================================================
    # AVAILABLE BUSES
    # ========================================================

    def available_buses(self):

        return sum(
            not bus.active
            for bus in self.buses
        )


    # ========================================================
    # ACTIVE BUSES
    # ========================================================

    def active_buses(self):

        return sum(
            bus.active
            for bus in self.buses
        )


    # ========================================================
    # PASSENGERS LEAVING BUS
    # ========================================================

    def passengers_leave(self, bus):

        if bus.passengers <= 0:

            return 0

        # Simplified assumption:
        # 10–30% of passengers leave at each zone.

        leaving = round(
            bus.passengers
            * random.uniform(
                0.10,
                0.30
            )
        )

        leaving = min(
            leaving,
            bus.passengers
        )

        bus.passengers -= leaving

        return leaving


    # ========================================================
    # BOARD PASSENGERS
    # ========================================================

    def board_passengers(self, bus):

        zone = bus.zone

        available_capacity = (
            BUS_CAPACITY
            - bus.passengers
        )

        if available_capacity <= 0:

            return 0

        waiting = self.waiting[zone]

        boarded = min(
            waiting,
            available_capacity
        )

        # Remove passengers from queue
        self.waiting[zone] -= boarded

        # Add passengers to bus
        bus.passengers += boarded

        # Statistics
        self.total_served += boarded

        bus.total_passengers_served += boarded

        # Revenue
        revenue = (
            boarded
            * FARE_PER_PASSENGER
        )

        bus.revenue += revenue

        self.total_revenue += revenue

        return boarded


    # ========================================================
    # MOVE BUSES
    # ========================================================

    def move_buses(self):

        completed_trips = []

        for bus in self.buses:

            if not bus.active:

                continue

            # ------------------------------------------------
            # 1. Passengers leave
            # ------------------------------------------------

            self.passengers_leave(bus)

            # ------------------------------------------------
            # 2. Waiting passengers board
            # ------------------------------------------------

            self.board_passengers(bus)

            # ------------------------------------------------
            # 3. Operating cost
            # ------------------------------------------------

            bus.operating_cost += COST_PER_STEP

            self.total_cost += COST_PER_STEP

            # ------------------------------------------------
            # 4. Move to next Ring Road zone
            # ------------------------------------------------

            bus.position += 1

            # ------------------------------------------------
            # 5. Full loop completed
            # ------------------------------------------------

            if bus.position >= len(ZONES):

                bus.position = 0

                bus.active = False

                bus.trips_completed += 1

                self.completed_trips += 1

                completed_trips.append(
                    bus.bus_id
                )

        return completed_trips


    # ========================================================
    # UPDATE WAITING TIME
    # ========================================================

    def update_waiting_time(self):

        step_waiting_time = 0

        for zone in self.zones:

            passengers = self.waiting[zone]

            # Every waiting passenger waits another
            # STEP_MINUTES minutes.

            additional_waiting = (
                passengers
                * STEP_MINUTES
            )

            self.waiting_time[zone] += (
                additional_waiting
            )

            step_waiting_time += (
                additional_waiting
            )

        return step_waiting_time


    # ========================================================
    # CURRENT AVERAGE OCCUPANCY
    # ========================================================

    def average_occupancy(self):

        active_buses = [
            bus
            for bus in self.buses
            if bus.active
        ]

        if not active_buses:

            return 0.0

        return (
            sum(
                bus.occupancy
                for bus in active_buses
            )
            / len(active_buses)
        )


    # ========================================================
    # CALCULATE REWARD
    # ========================================================

    def calculate_reward(
        self,
        step_profit,
        step_waiting_time,
    ):

        # ----------------------------------------------------
        # 1. Waiting penalty
        # ----------------------------------------------------

        waiting_penalty = (
            step_waiting_time
            * 0.10
        )

        # ----------------------------------------------------
        # 2. Occupancy penalty
        # ----------------------------------------------------

        occupancy = (
            self.average_occupancy()
        )

        target_occupancy = 0.85

        # Penalize buses that are far from 85%
        occupancy_penalty = (
            abs(
                occupancy
                - target_occupancy
            )
            * 10
        )

        # ----------------------------------------------------
        # 3. Profit reward
        # ----------------------------------------------------

        profit_reward = (
            step_profit
            * 0.05
        )

        # ----------------------------------------------------
        # Final reward
        # ----------------------------------------------------

        reward = (
            -waiting_penalty
            -occupancy_penalty
            +profit_reward
        )

        return reward


    # ========================================================
    # MAIN ENVIRONMENT STEP
    # ========================================================

    def step(
        self,
        dispatch_count=0
    ):

        # ----------------------------------------------------
        # Save previous profit
        # ----------------------------------------------------

        previous_profit = (
            self.total_profit
        )

        # ----------------------------------------------------
        # 1. Generate new passenger demand
        # ----------------------------------------------------

        arrivals = (
            self.generate_passengers()
        )

        # ----------------------------------------------------
        # 2. Dispatch buses from Gongabu
        # ----------------------------------------------------

        dispatched = []

        for _ in range(
            dispatch_count
        ):

            bus_id = (
                self.dispatch_bus()
            )

            if bus_id is not None:

                dispatched.append(
                    bus_id
                )

                self.last_dispatch_time = (
                    self.time
                )

        # ----------------------------------------------------
        # 3. Move buses
        # ----------------------------------------------------

        completed = (
            self.move_buses()
        )

        # ----------------------------------------------------
        # 4. Calculate waiting time
        # ----------------------------------------------------

        step_waiting_time = (
            self.update_waiting_time()
        )

        # ----------------------------------------------------
        # 5. Calculate total profit
        # ----------------------------------------------------

        self.total_profit = (
            self.total_revenue
            - self.total_cost
        )

        # ----------------------------------------------------
        # 6. Calculate profit generated this step
        # ----------------------------------------------------

        step_profit = (
            self.total_profit
            - previous_profit
        )

        # ----------------------------------------------------
        # 7. Reward
        # ----------------------------------------------------

        reward = self.calculate_reward(
            step_profit=step_profit,
            step_waiting_time=step_waiting_time,
        )

        # ----------------------------------------------------
        # 8. Advance simulation clock
        # ----------------------------------------------------

        self.time += 1

        # ----------------------------------------------------
        # 9. Return state information
        # ----------------------------------------------------

        state = self.get_state()

        return state, reward


    # ========================================================
    # RL STATE
    # ========================================================

    def get_rl_state(self):

        # ----------------------------------------------------
        # 1. Waiting level
        # ----------------------------------------------------

        total_waiting = sum(
            self.waiting.values()
        )

        if total_waiting < 30:

            waiting_level = 0

        elif total_waiting < 70:

            waiting_level = 1

        else:

            waiting_level = 2

        # ----------------------------------------------------
        # 2. Demand level
        # ----------------------------------------------------

        if self.time == 0:

            average_demand = 0

        else:

            average_demand = (
                self.total_arrivals
                / self.time
                / len(self.zones)
            )

        if average_demand < 8:

            demand_level = 0

        elif average_demand < 14:

            demand_level = 1

        else:

            demand_level = 2

        # ----------------------------------------------------
        # 3. Available buses
        # ----------------------------------------------------

        available = (
            self.available_buses()
        )

        if available <= 4:

            available_level = 0

        elif available <= 10:

            available_level = 1

        else:

            available_level = 2

        # ----------------------------------------------------
        # 4. Active buses
        # ----------------------------------------------------

        active = (
            self.active_buses()
        )

        if active <= 5:

            active_level = 0

        elif active <= 12:

            active_level = 1

        else:

            active_level = 2

        # ----------------------------------------------------
        # 5. Average occupancy
        # ----------------------------------------------------

        occupancy = (
            self.average_occupancy()
        )

        if occupancy < 0.60:

            occupancy_level = 0

        elif occupancy < 0.80:

            occupancy_level = 1

        else:

            occupancy_level = 2

        # ----------------------------------------------------
        # 6. Headway
        # ----------------------------------------------------

        headway = (
            self.time
            - self.last_dispatch_time
        )

        if headway <= 2:

            headway_level = 0

        elif headway <= 4:

            headway_level = 1

        else:

            headway_level = 2

        # ----------------------------------------------------
        # Final discrete state
        # ----------------------------------------------------

        return (
            demand_level,
            waiting_level,
            available_level,
            active_level,
            occupancy_level,
            headway_level,
        )


    # ========================================================
    # FULL ENVIRONMENT STATE
    # ========================================================

    def get_state(self):

        return {

            # ----------------------------------------------
            # Simulation
            # ----------------------------------------------

            "time_step":
                self.time,

            "time":
                round(
                    self.current_hour(),
                    2
                ),

            # ----------------------------------------------
            # Passenger information
            # ----------------------------------------------

            "waiting":
                self.waiting.copy(),

            "total_waiting":
                sum(
                    self.waiting.values()
                ),

            "total_arrivals":
                self.total_arrivals,

            "total_served":
                self.total_served,

            # ----------------------------------------------
            # Fleet
            # ----------------------------------------------

            "available_buses":
                self.available_buses(),

            "active_buses":
                self.active_buses(),

            "average_occupancy":
                round(
                    self.average_occupancy()
                    * 100,
                    2
                ),

            # ----------------------------------------------
            # Operations
            # ----------------------------------------------

            "completed_trips":
                self.completed_trips,

            # ----------------------------------------------
            # Finance
            # ----------------------------------------------

            "revenue":
                round(
                    self.total_revenue,
                    2
                ),

            "cost":
                round(
                    self.total_cost,
                    2
                ),

            "profit":
                round(
                    self.total_profit,
                    2
                ),

            # ----------------------------------------------
            # Last dispatch
            # ----------------------------------------------

            "last_dispatch_time":
                self.last_dispatch_time,

            # ----------------------------------------------
            # Individual buses
            # ----------------------------------------------

            "buses": [

                {

                    "id":
                        bus.bus_id,

                    "zone":
                        bus.zone,

                    "position":
                        bus.position,

                    "passengers":
                        bus.passengers,

                    "capacity":
                        BUS_CAPACITY,

                    "occupancy":
                        round(
                            bus.occupancy * 100,
                            2
                        ),

                    "active":
                        bus.active,

                    "trips_completed":
                        bus.trips_completed,

                }

                for bus in self.buses
            ],
        }