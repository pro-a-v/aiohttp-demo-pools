import argparse
import asyncio
import logging
import sys

import jinja2

import aiohttp_jinja2
from aiohttp import web
from mydb import close_db, init_db
from middlewares import setup_middlewares
from routes import setup_routes
from utils import TRAFARET
from trafaret_config import commandline


def init(loop, argv):
    ap = argparse.ArgumentParser()
    commandline.standard_argparse_options(ap, default_config='./config/polls.yaml')
    #
    # define your command-line arguments here
    #
    options = ap.parse_args(argv)

    config = commandline.config_from_options(options, TRAFARET)

    # setup application and extensions
    app = web.Application(loop=loop)

    # load config from yaml file in current dir
    app['config'] = config

    # setup Jinja2 template renderer
    print(jinja2.FileSystemLoader('./templates').list_templates())
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

    # create connection to the database
    app.on_startup.append(init_db)
    # shutdown db connection on exit
    app.on_cleanup.append(close_db)
    # setup views and routes
    myargs = {'path': {'client_id' : 1 }}
    asd = str('/pool/{client_id}').format_map(myargs['path'])
    setup_routes(app)
    setup_middlewares(app)
    return app


def main(argv):
    # init logging
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()

    app = init(loop, argv)
    web.run_app(app, host=app['config']['host'], port=app['config']['port'])


if __name__ == '__main__':
    main(sys.argv[1:])
