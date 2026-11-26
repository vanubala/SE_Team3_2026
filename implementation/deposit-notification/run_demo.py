"""Run the UC3 localhost demo. This does not connect to real locker hardware."""
import logging

from dotenv import load_dotenv
import uvicorn

from deposit_notification.demo import create_demo_app


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    app = create_demo_app()
    print("UC3 demo running at http://127.0.0.1:8000/docs")
    print(f"Demo locker ID: {app.state.demo_locker_id}")
    print(f"Demo compartment ID: {app.state.demo_compartment_id}")
    print(f"Demo parcel ID: {app.state.demo_parcel_id}")
    print("Demo terminal header X-Demo-Locker-ID: <the demo locker ID>")
    uvicorn.run(app, host="127.0.0.1", port=8000)
