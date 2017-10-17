import aiohttp_jinja2
from aiohttp import web

from mydb import get_question, question, vote as dbvote, RecordNotFound


@aiohttp_jinja2.template('index.html')
async def index(request):
    async with request.app['db'].acquire() as conn:
        #cursor = await conn.execute('select question.id as id, question.question_text as question_text , question.pub_date as pub_date,  choice.choice_text as choice_text, choice.votes as votes , choice.question_id as question_id from question,choice where question.id=question.id')
        cursor = await conn.execute(question.select() )
        records = await cursor.fetchall()
        questions = [dict(q) for q in records]
        return {'questions': questions}


@aiohttp_jinja2.template('detail.html')
async def poll(request):
    async with request.app['db'].acquire() as conn:
        question_id = request.match_info['question_id']
        try:

            question, choices = await get_question(conn, question_id)
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))
        return {
            'question': question,
            'choices': choices
        }


@aiohttp_jinja2.template('results.html')
async def results(request):
    async with request.app['db'].acquire() as conn:
        question_id = request.match_info['question_id']

        try:

            question, choices = await get_question(conn,  question_id)
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))

        return {
            'question': question,
            'choices': choices
        }


async def vote(request):
    async with request.app['db'].acquire() as conn:
        question_id = int(request.match_info['question_id'])
        data = await request.post()
        try:
            choice_id = int(data['choice'])
        except (KeyError, TypeError, ValueError) as e:
            raise web.HTTPBadRequest(
                text='You have not specified choice value') from e
        try:
            await dbvote(conn, question_id, choice_id)
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))
        router = request.app.router
        url = router['results'].url(parts={'question_id': question_id})
        return web.HTTPFound(location=url)
