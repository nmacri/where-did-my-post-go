import app
import random

post_generator = app.post_generator()

if random.randint(1,3) == 1:
	post_generator.publish_best_submission()

etl_controller = app.etl_controller()
etl_controller.tb_reblog_tree_etl_targets()


