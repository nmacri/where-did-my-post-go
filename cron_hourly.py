import app
etl_controller = app.etl_controller()

etl_controller.check_submissions()

etl_controller.tb_reblog_tree_etl_active_posts()