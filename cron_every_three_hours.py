import app

etl_controller = app.etl_controller()
etl_controller.tb_reblog_tree_etl_targets()

post_generator = app.post_generator()
post_generator.generate_photo_posts(count = 4)