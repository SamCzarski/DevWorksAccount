# import logging
#
# from devworks_hydra.rest import Logout
#
# from DevWorksAccount import celery_app
#
# log = logging.getLogger(__name__)
#
#
# @celery_app.task(name="hydra_forced_logout")
# def hydra_forced_logout(hydra_subject):
#     log.info("Force logging out of hydra subject id: {}".format(hydra_forced_logout))
#     test_ep = Logout()
#     return test_ep.force(hydra_subject)
#
