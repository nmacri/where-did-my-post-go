import app
import random

post_generator = app.post_generator()

if random.random() < .625:
	try:
		post_generator.publish_best_submission()
	except:
		pass

etl_controller = app.etl_controller()
etl_controller.tb_reblog_tree_etl_targets()


