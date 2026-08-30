import gymnasium as gym
from gymnasium import spaces
import numpy as np

class RingRoadEnv(gym.Env):
    """
    A Simple environment for ring road public bus traffic simulation

    Simulated Bus Stops:
        Gongabu
        Balaju
        Kalanki
        Balkhu
        Satdobato
        Koteshwor
        Tinkune
        Chabahil
        Gongabu
    
    Goals:
        1. Minimize passenger waiting time
        2. Keep buses reasonably full
        3. Maximize profit
    
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, render=None):
        super().__init__()

        #Road Zones

        self.zones = [
            "Gongabu",
            "Balaju",
            "Kalanki",
            "Balkhu",
            "Satdobato",
            "Koteshwor",
            "Tinkune",
            "Chabahil",
        ]

        # Environment Parameters    
        self.num_zones = len(self.zones)
        self.segment_time = 5
        self.step_minutes = 5
        self.max_steps = 192

        # Fare setup
        self.fare_per_passenger = 30
        self.cost_per_bus_per_step = 40

        # Base passenger demands

        self.base_demand = np.array([
            10,  # Gongabu
            7,   # Balaju
            12,  # Kalanki
            8,   # Balkumari
            9,   # Satdobato
            14,  # Koteshwor
            8,   # Tinkune
            10,  # Chabahil
        ], dtype=np.float32)


        
        # ACTION SPACE
        

        # 0 -> dispatch 0 buses
        # 1 -> dispatch 1 bus
        # 2 -> dispatch 2 buses
        # 3 -> dispatch 3 buses

        self.action_space = spaces.Discrete(4)

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.num_zones * 4 + 3,),
            dtype=np.float32,
        )


        # OBSERVATION SPACE


            # For every zone we provide:
            
            # 1. Current waiting passengers
            # 2. Expected future demand
            # 3. ETA of nearest bus
            # 4. Estimated unmet demand
            
            # With :

            # 5. Available buses
            # 6. Active buses
            # 7. Average occupancy


        #Internal state representation

        self.current_step = 0

        self.waiting = None
        self.buses = []

        self.total_arrivals = 0
        self.total_served = 0
        self.total_revenue = 0
        self.total_cost = 0
        self.total_waiting_time = 0
        self.total_fleet = 10
        self.bus_capacity = 50




     #Reset

    def reset(self, *, seed=None, options=None):

        super().reset(seed=seed)

        self.current_step = 0

        # Waiting passengers at each zone
        self.waiting = np.zeros(
            self.num_zones,
            dtype=np.float32,
        )

        # List of active buses
        self.buses = []

        # Statistics
        self.total_arrivals = 0
        self.total_served = 0
        self.total_revenue = 0
        self.total_cost = 0
        self.total_waiting_time = 0

        observation = self._get_observation()

        info = self._get_info()

        return observation, info

    # ======================================================
    # TIME
    # ======================================================

    def _current_hour(self):

        minutes = (
            self.current_step
            * self.step_minutes
        )

        return 6 + minutes / 60
    

    def _demand_multiplier(self):

        hour = self._current_hour()

        # Morning peak
        if 7 <= hour < 9:
            return 1.8

        # Evening peak
        if 16 <= hour < 19:
            return 1.8

        # Lower midday demand
        if 10 <= hour < 15:
            return 0.8

        return 1.0
    

    # GENERATE PASSENGER DEMAND

    def _generate_demand(self):

        multiplier = self._demand_multiplier()

        expected_demand = (
            self.base_demand
            * multiplier
        )

        arrivals = self.np_random.poisson(
            expected_demand
        )

        self.waiting += arrivals

        self.total_arrivals += int(
            arrivals.sum()
        )

        return arrivals


     # DISPATCH BUS FROM GONGABU

    def _dispatch_bus(self):

        if len(self.buses) >= self.total_fleet:
            return False

        bus = {
            "id": self._next_bus_id(),
            "position": 0,
            "passengers": 0,
        }

        self.buses.append(bus)

        return True

    
     # BUS ID

    def _next_bus_id(self):

        if not self.buses:
            return 1

        return max(
            bus["id"]
            for bus in self.buses
        ) + 1
    
    #Move bus

    def _move_buses(self):

        for bus in self.buses:

            # Move one zone every simulation step
            bus["position"] += 1

            # After completion reset positon on gongabu
            if bus["position"] >= self.num_zones:
                bus["position"] = 0
                bus["passengers"] = 0

    
    # PASSENGER PROCESSING
    def _process_passengers(self):

        total_boarded = 0

        for bus in self.buses:

            zone = bus["position"]


            # passenger leaving simulation
            if bus["passengers"] > 0:

                leaving_ratio = self.np_random.uniform(
                    0.10,
                    0.30,
                )

                leaving = int(
                    bus["passengers"]
                    * leaving_ratio
                )

                bus["passengers"] -= leaving


            available_capacity = (
                self.bus_capacity
                - bus["passengers"]
            )

     
            waiting = self.waiting[zone]

            # Passengers can board
            boarded = min(
                waiting,
                available_capacity,
            )

            self.waiting[zone] -= boarded

            bus["passengers"] += boarded

            total_boarded += int(boarded)

            self.total_served += int(boarded)

            # Revenue
            self.total_revenue += (
                boarded
                * self.fare_per_passenger
            )

        return total_boarded
    
    #Find nearest bus to the zone
    def _nearest_bus(self, zone):

        if not self.buses:
            return None

        nearest_bus = None
        nearest_distance = float("inf")

        for bus in self.buses:

            current_position = bus["position"]

            # Ring-road distance
            distance = (
                zone
                - current_position
            ) % self.num_zones

            if distance < nearest_distance:

                nearest_distance = distance
                nearest_bus = bus

        return nearest_bus
    
    
    #Bus Expected Time of Arrival (ETA) to the zone
    def _nearest_bus_eta(self, zone):

        if not self.buses:
            return None

        nearest_distance = float("inf")

        for bus in self.buses:

            distance = (
                zone
                - bus["position"]
            ) % self.num_zones

            nearest_distance = min(
                nearest_distance,
                distance,
            )

        return (
            nearest_distance
            * self.segment_time
        )


    #Expected future demand
    def _expected_future_demand(self, zone):

        eta = self._nearest_bus_eta(zone)

    
        if eta is None:
            eta = 30

        steps_until_arrival = max(
            1,
            int(
                np.ceil(
                    eta
                    / self.step_minutes
                )
            ),
        )

        multiplier = self._demand_multiplier()

        demand_per_step = (
            self.base_demand[zone]
            * multiplier
        )

        expected = (
            demand_per_step
            * steps_until_arrival
        )

        return float(expected)
    


    #Estimate UMET demand

    def _estimate_unmet_demand(self, zone):

        current_waiting = (
            self.waiting[zone]
        )

        future_demand = (
            self._expected_future_demand(zone)
        )

        bus = self._nearest_bus(zone)


        if bus is None:
            available_capacity = 0

        else:
            available_capacity = (
                self.bus_capacity
                - bus["passengers"]
            )

        expected_total = (
            current_waiting
            + future_demand
        )

        unmet = max(
            0,
            expected_total
            - available_capacity,
        )

        return float(unmet)
    
    #Waiting time
    def _calculate_waiting_time(self):

        waiting_passengers = (
            self.waiting.sum()
        )

        waiting_time = (
            waiting_passengers
            * self.step_minutes
        )

        self.total_waiting_time += (
            waiting_time
        )

        return float(waiting_time)
    
    def _average_occupancy(self):

        if not self.buses:
            return 0.0

        occupancies = []

        for bus in self.buses:

            occupancy = (
                bus["passengers"]
                / self.bus_capacity
            )

            occupancies.append(
                occupancy
            )

        return float(
            np.mean(occupancies)
        )
    
    def _calculate_reward(self,waiting_time,):


        waiting_penalty = (waiting_time* 0.1)

        occupancy = (self._average_occupancy())

        target_occupancy = 0.85

        occupancy_penalty = (
            abs(occupancy - target_occupancy)* 10)

        profit = (self.total_revenue- self.total_cost)

        profit_reward = (profit* 0.01)

        reward = (profit_reward - waiting_penalty - occupancy_penalty)
        return float(reward)
        
    #Observation
    def _get_observation(self):

        observation = []

        for zone in range(
            self.num_zones
        ):

            # Current passengers waiting
            waiting = (
                self.waiting[zone]
            )

            # Future demand
            future_demand = (
                self._expected_future_demand(
                    zone
                )
            )

            # Bus ETA
            eta = (
                self._nearest_bus_eta(
                    zone
                )
            )

            if eta is None:
                eta = 30.0

            # Potential unmet demand
            unmet = (
                self._estimate_unmet_demand(
                    zone
                )
            )

            observation.extend([
                waiting,
                future_demand,
                eta,
                unmet,
            ])

        # Global state
        available_buses = (
            self.total_fleet
            - len(self.buses)
        )

        active_buses = len(
            self.buses
        )

        occupancy = (
            self._average_occupancy()
        )

        observation.extend([
            available_buses,
            active_buses,
            occupancy,
        ])

        return np.array(
            observation,
            dtype=np.float32,
        )
    
    # STEP
    def step(self, action):

        action = int(action)

        arrivals = (
            self._generate_demand()
        )

    
        dispatched = 0

        for _ in range(action):

            if self._dispatch_bus():

                dispatched += 1

    
        boarded = (
            self._process_passengers()
        )

    
        waiting_time = (
            self._calculate_waiting_time()
        )

   
        step_cost = (
            len(self.buses)
            * self.cost_per_bus_per_step
        )

        self.total_cost += step_cost

        # --------------------------------------------------
        # 6. Move buses
        # --------------------------------------------------

        self._move_buses()

        # --------------------------------------------------
        # 7. Reward
        # --------------------------------------------------

        reward = (
            self._calculate_reward(
                waiting_time
            )
        )

        # --------------------------------------------------
        # 8. Advance simulation time
        # --------------------------------------------------

        self.current_step += 1

        # --------------------------------------------------
        # 9. Episode termination
        # --------------------------------------------------

        terminated = (
            self.current_step
            >= self.max_steps
        )

        truncated = False

        # --------------------------------------------------
        # 10. Observation
        # --------------------------------------------------

        observation = (
            self._get_observation()
        )

        # --------------------------------------------------
        # 11. Information for UI/debugging
        # --------------------------------------------------

        info = self._get_info()

        info["arrivals"] = arrivals
        info["boarded"] = boarded
        info["dispatched"] = dispatched
        info["waiting_time"] = waiting_time

        return (
            observation,
            reward,
            terminated,
            truncated,
            info,
        )

  #Info about environment
    def _get_info(self):

        zone_predictions = []

        for zone in range(
            self.num_zones
        ):

            zone_predictions.append({

                "zone":
                    self.zones[zone],

                "waiting":
                    float(
                        self.waiting[zone]
                    ),

                "future_demand":
                    self._expected_future_demand(
                        zone
                    ),

                "bus_eta":
                    self._nearest_bus_eta(
                        zone
                    ),

                "unmet_demand":
                    self._estimate_unmet_demand(
                        zone
                    ),
            })

        bus_information = []

        for bus in self.buses:

            bus_information.append({

                "id":
                    bus["id"],

                "zone":
                    self.zones[
                        bus["position"]
                    ],

                "position":
                    bus["position"],

                "passengers":
                    bus["passengers"],

                "capacity":
                    self.bus_capacity,

                "occupancy":
                    (
                        bus["passengers"]
                        / self.bus_capacity
                    ),
            })

        return {

            "time":
                self._current_hour(),

            "total_waiting":
                int(
                    self.waiting.sum()
                ),

            "active_buses":
                len(self.buses),

            "available_buses":
                (
                    self.total_fleet
                    - len(self.buses)
                ),

            "occupancy":
                self._average_occupancy(),

            "total_arrivals":
                self.total_arrivals,

            "total_served":
                self.total_served,

            "revenue":
                self.total_revenue,

            "cost":
                self.total_cost,

            "profit":
                (
                    self.total_revenue
                    - self.total_cost
                ),

            "buses":
                bus_information,

            "zone_predictions":
                zone_predictions,
        }


    # Render environment

    def render(self):

        print()
        print("=" * 70)
        print("TRANSITOPT - KATHMANDU RING ROAD")
        print("=" * 70)

        print(
            f"Time: "
            f"{self._current_hour():.2f}"
        )

        print(
            f"Waiting passengers: "
            f"{self.waiting.sum():.0f}"
        )

        print(
            f"Active buses: "
            f"{len(self.buses)}"
        )

        print(
            f"Available buses: "
            f"{self.total_fleet - len(self.buses)}"
        )

        print(
            f"Average occupancy: "
            f"{self._average_occupancy() * 100:.1f}%"
        )

        print()

        print("BUSES")
        print("-" * 70)

        for bus in self.buses:

            print(
                f"Bus {bus['id']:02d} | "
                f"{self.zones[bus['position']]:<12} | "
                f"{bus['passengers']:02d}/"
                f"{self.bus_capacity}"
            )

        print()

        print("ZONE DEMAND")
        print("-" * 70)

        for zone in range(
            self.num_zones
        ):

            eta = (
                self._nearest_bus_eta(
                    zone
                )
            )

            print(
                f"{self.zones[zone]:<12} | "
                f"Waiting: "
                f"{self.waiting[zone]:5.0f} | "
                f"Future: "
                f"{self._expected_future_demand(zone):5.1f} | "
                f"ETA: "
                f"{str(eta):>5} min | "
                f"Unmet: "
                f"{self._estimate_unmet_demand(zone):5.1f}"
            )

        print("=" * 70)


    #Close Simulation
    def close(self):
        pass




if __name__ == "__main__":
    env = RingRoadEnv()
    print(env.base_demand)
    print("Environment initialized successfully.")

        



