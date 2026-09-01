from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import numpy as np
import random
import os

from environment import RingRoadEnv
from train import discretize_state



# FASTAPI


app = FastAPI(
    title="TransitOptimizer API",
    description="Kathmandu Ring Road Public Bus RL Simulation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

Q_TABLE_PATH = os.path.join(BASE_DIR, "q_table.npy")


#Load Q Table 
def load_q_table():

    if not os.path.exists(Q_TABLE_PATH):

        raise FileNotFoundError(
            "q_table.npy not found. "
            "Run train.py first."
        )

    q_table = np.load(Q_TABLE_PATH)
    print(q_table)

    return q_table



# Load once when backend starts
try:

    Q_TABLE = load_q_table()

    print(
        f"Q-table loaded successfully: "
        f"{Q_TABLE.shape}"
    )

except Exception as e:

    Q_TABLE = None

    print(
        f"WARNING: Could not load Q-table: {e}"
    )


# ============================================================
# REQUEST MODEL
# ============================================================

class StepRequest(BaseModel):

    # None means use the trained Q-table
    action: int | None = None


# ============================================================
# Q-LEARNING ACTION
# ============================================================

def q_action(
    q_table,
    observation,
):

    # Convert continuous observation
    # into the same discrete state
    # used during training.

    state = discretize_state(
        observation
    )

    # Get Q-values for this state

    q_values = q_table[state]

    # Select action with highest Q-value

    action = int(
        np.argmax(q_values)
    )

    return action


# ============================================================
# FIXED-DISPATCH POLICY
# ============================================================

# The direct baseline always keeps this many buses on the road.
FIXED_ACTIVE_BUSES = 7


def direct_action(
    observation,
    env,
):

    """
    Fixed baseline policy: exactly 7 buses are always kept on
    the road. Each step the number of buses needed to reach that
    fixed fleet is launched (they loop the ring and are re-launched
    as they return to the depot).
    """

    active = len(env.buses)

    return max(
        0,
        FIXED_ACTIVE_BUSES - active,
    )


# ============================================================
# SERIALIZE ENVIRONMENT INFO
# ============================================================

def serialize_value(
    value
):

    """
    Recursively convert numpy values to
    plain Python types (JSON-safe).
    """

    if isinstance(
        value,
        np.ndarray
    ):

        return value.tolist()

    if isinstance(
        value,
        np.integer
    ):

        return int(value)

    if isinstance(
        value,
        np.floating
    ):

        return float(value)

    if isinstance(
        value,
        dict
    ):

        return {
            k: serialize_value(v)
            for k, v in value.items()
        }

    if isinstance(
        value,
        list
    ):

        return [
            serialize_value(item)
            for item in value
        ]

    return value


def serialize_info(
    info
):

    if isinstance(
        info,
        list
    ):

        return [
            serialize_value(item)
            for item in info
        ]

    result = {}

    for key, value in info.items():

        result[key] = (
            serialize_value(
                value
            )
        )

    return result


# ============================================================
# SIMULATION MANAGER
# ============================================================

class SimulationManager:

    def __init__(self):

        self.q_env = None

        self.direct_env = None

        self.q_observation = None

        self.direct_observation = None

        self.reset()


    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        seed=42
    ):

        self.q_env = RingRoadEnv()

        self.direct_env = RingRoadEnv()

        (
            self.q_observation,
            _
        ) = self.q_env.reset(
            seed=seed
        )

        (
            self.direct_observation,
            _
        ) = self.direct_env.reset(
            seed=seed
        )


    # ========================================================
    # CONVERT INFO FOR FRONTEND
    # ========================================================

    def get_state(
        self,
        env,
        observation,
        action=None,
        reward=None,
    ):

        info = env._get_info()

        return {

            "time": float(
                info["time"]
            ),

            "time_label":
                self.format_time(
                    info["time"]
                ),

            "step": int(
                info["step"]
            ),

            "action": action,

            "reward":
                float(
                    reward or 0
                ),

            "total_waiting":
                int(
                    info[
                        "total_waiting"
                    ]
                ),

            "active_buses":
                int(
                    info[
                        "active_buses"
                    ]
                ),

            "available_buses":
                int(
                    info[
                        "available_buses"
                    ]
                ),

            "occupancy":
                float(
                    info[
                        "occupancy"
                    ]
                ),

            "occupancy_percent":
                float(
                    info[
                        "occupancy"
                    ] * 100
                ),

            "total_arrivals":
                int(
                    info[
                        "total_arrivals"
                    ]
                ),

            "total_served":
                int(
                    info[
                        "total_served"
                    ]
                ),

            "total_left":
                int(
                    info[
                        "total_left"
                    ]
                ),

            "revenue":
                float(
                    info[
                        "revenue"
                    ]
                ),

            "cost":
                float(
                    info[
                        "cost"
                    ]
                ),

            "profit":
                float(
                    info[
                        "profit"
                    ]
                ),

            "buses":
                serialize_info(
                    info[
                        "buses"
                    ]
                ),

            "zone_predictions":
                serialize_info(
                    info[
                        "zone_predictions"
                    ]
                ),
        }


    # ========================================================
    # TIME FORMAT
    # ========================================================

    @staticmethod
    def format_time(
        hour
    ):

        hours = int(
            hour
        )

        minutes = int(
            round(
                (hour - hours)
                * 60
            )
        )

        if minutes >= 60:

            hours += 1

            minutes = 0

        return (
            f"{hours:02d}:"
            f"{minutes:02d}"
        )


    # ========================================================
    # STEP BOTH SIMULATIONS
    # ========================================================

    def step(
        self,
        manual_q_action=None
    ):

        # ----------------------------------------------------
        # Make sure Q-table exists
        # ----------------------------------------------------

        if Q_TABLE is None:

            raise RuntimeError(
                "Q-table is not loaded."
            )

        # ----------------------------------------------------
        # Q-LEARNING ACTION
        # ----------------------------------------------------

        if manual_q_action is None:

            q_action_value = q_action(
                Q_TABLE,
                self.q_observation
            )

        else:

            q_action_value = int(
                manual_q_action
            )

        # ----------------------------------------------------
        # Validate action
        # ----------------------------------------------------

        if q_action_value < 0:

            raise ValueError(
                "Action cannot be negative."
            )

        if q_action_value >= 4:

            raise ValueError(
                "Action must be 0, 1, 2 or 3."
            )

        # ----------------------------------------------------
        # DIRECT ACTION
        # ----------------------------------------------------

        direct_action_value = direct_action(
            self.direct_observation,
            self.direct_env
        )

        (
            self.q_observation,
            q_reward,
            q_terminated,
            q_truncated,
            q_info
        ) = self.q_env.step(
            q_action_value
        )

        # ----------------------------------------------------
        # STEP DIRECT ENVIRONMENT
        # ----------------------------------------------------

        (
            self.direct_observation,
            direct_reward,
            direct_terminated,
            direct_truncated,
            direct_info
        ) = self.direct_env.step(
            direct_action_value,
            fixed_dispatch=(
                direct_action_value
            ),
        )

        # ----------------------------------------------------
        # Auto-reset when either env reaches 22:00
        # ----------------------------------------------------

        reset_happened = False

        if q_terminated or direct_terminated:

            self.reset()

            reset_happened = True

        # ----------------------------------------------------
        # Prepare response
        # ----------------------------------------------------

        q_state = self.get_state(
            self.q_env,
            self.q_observation,
            q_action_value,
            q_reward
        )

        direct_state = self.get_state(
            self.direct_env,
            self.direct_observation,
            direct_action_value,
            direct_reward
        )

        # ----------------------------------------------------
        # Comparison
        # ----------------------------------------------------

        profit_difference = (
            q_state["profit"]
            -
            direct_state["profit"]
        )

        waiting_difference = (
            q_state["total_waiting"]
            -
            direct_state[
                "total_waiting"
            ]
        )

        occupancy_difference = (
            q_state["occupancy"]
            -
            direct_state[
                "occupancy"
            ]
        )

        return {

            "q_learning":
                q_state,

            "direct":
                direct_state,

            "comparison": {

                "profit_difference":
                    profit_difference,

                "waiting_difference":
                    waiting_difference,

                "occupancy_difference":
                    occupancy_difference,

                "q_better_profit":
                    profit_difference > 0,

            },

            "terminated":
                False,

            "truncated":
                False,

            "reset":
                reset_happened,
        }


# ============================================================
# CREATE SIMULATION
# ============================================================

simulation = SimulationManager()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    index_path = os.path.join(
        BASE_DIR,
        "index.html"
    )

    if os.path.exists(
        index_path
    ):

        return FileResponse(
            index_path
        )

    return {

        "name":
            "TransitOptimizer",

        "status":
            "running",

        "q_table_loaded":
            Q_TABLE is not None,

        "q_table_shape":
            (
                list(
                    Q_TABLE.shape
                )
                if Q_TABLE is not None
                else None
            ),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():

    return {

        "status":
            "ok",

        "q_table_loaded":
            Q_TABLE is not None,

        "q_table_shape":
            (
                list(
                    Q_TABLE.shape
                )
                if Q_TABLE is not None
                else None
            ),

        "q_table_path":
            Q_TABLE_PATH,
    }


# ============================================================
# RESET
# ============================================================

@app.post("/api/simulation/reset")
def reset():

    simulation.reset(
        seed=42
    )

    return {

        "q_learning":
            simulation.get_state(
                simulation.q_env,
                simulation.q_observation
            ),

        "direct":
            simulation.get_state(
                simulation.direct_env,
                simulation.direct_observation
            ),
    }


# ============================================================
# STEP
# ============================================================

@app.post(
    "/api/simulation/step"
)
def simulation_step(
    request: StepRequest
):

    try:

        return simulation.step(
            request.action
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# CURRENT STATE
# ============================================================

@app.get(
    "/api/simulation"
)
def current_simulation():

    return {

        "q_learning":
            simulation.get_state(
                simulation.q_env,
                simulation.q_observation
            ),

        "direct":
            simulation.get_state(
                simulation.direct_env,
                simulation.direct_observation
            ),
    }


# ============================================================
# INSPECT Q-TABLE STATE
# ============================================================

@app.get(
    "/api/q-table/{state}"
)
def inspect_q_table(
    state: int
):

    if Q_TABLE is None:

        raise HTTPException(
            status_code=500,
            detail="q_table.npy not loaded."
        )

    if state < 0 or state >= len(
        Q_TABLE
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid state {state}. "
                f"Valid range: "
                f"0-{len(Q_TABLE)-1}"
            )
        )

    values = Q_TABLE[
        state
    ]

    return {

        "state":
            state,

        "q_values":
            values.tolist(),

        "best_action":
            int(
                np.argmax(values)
            ),

        "actions": {

            "0":
                "Dispatch 0 buses",

            "1":
                "Dispatch 1 bus",

            "2":
                "Dispatch 2 buses",

            "3":
                "Dispatch 3 buses",
        }
    }


# ============================================================
# STATIC FILES
# ============================================================

if os.path.exists(
    BASE_DIR
):

    app.mount(
        "/static",
        StaticFiles(
            directory=BASE_DIR
        ),
        name="static"
    )