import logging

from utils import *
import time

# # Enable logging
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )
# # Set higher logging level for httpx to avoid all GET and POST requests being logged
# logging.getLogger("httpx").setLevel(logging.WARNING)

# logger = logging.getLogger(__name__)

def main() -> None:
    #-------- sanitisation --------# 
    # remove followings records of handles no longer being tracked by users
    delete_unused_followings()

    #-------- driver and X.com account login setup --------# 
    # initiate driver
    tracker = driversetup()
    try:
        # perform X.com account login
        login_actions(driver=tracker)
        time.sleep(5) # enough time for page to propery sign in

        #-------- retrieve handles list  --------# 
        handles_list = [handle[0] for handle in get_handles_list()]

        #-------- for-loop to process for each handle  --------#
        
        start_time = time.time()

        for handle in handles_list:
            # check if handle is valid
            following_data = get_following_data(driver=tracker,handle_id=handle)

            if following_data:
                # check if there is existing following records for handle
                existing_followings = get_existing_followings(handle_id=handle)
                if existing_followings:
                    # updates existing following data
                    update_followings(handle_id=handle,followings_list=following_data,existing_followings=existing_followings)
                else:
                    # dumps initial following data
                    save_initial_followings(handle_id=handle,followings_list=following_data)
            else:
                # push notification to affected users about invalid handle
                invalid_handle_notif(handle)
        
        end_time = time.time()
        execution_time = end_time - start_time
        logging.warning(f"Execution time for handle for-loop: {execution_time:.6f} seconds")

        #-------- for-loop to send push new followings notifs to each user --------#
        send_following_notif()
    
    except BaseException:
        logging.exception("An exception was thrown!")
        tracker.save_screenshot('test.png')
    
    tracker.save_screenshot('test.png')
    tracker.quit()
    



if __name__ == "__main__":
    main()