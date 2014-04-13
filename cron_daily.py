import app
etl_controller = app.etl_controller()

etl_controller.tb_posts_etl()

etl_controller.etl_target_blog_reblog_graphs()

post_generator = app.post_generator()
post_generator.generate_photo_posts(count = 4)

