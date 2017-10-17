import aiomysql.sa
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

__all__ = ['question', 'choice']

meta = sa.MetaData()


question = sa.Table(
    'question', meta,
    sa.Column('id', sa.Integer, nullable=False),
    sa.Column('question_text', sa.String(200), nullable=False),
    sa.Column('pub_date', sa.Date, nullable=False)
)

choice = sa.Table(
    'choice', meta,
    sa.Column('id', sa.Integer, nullable=False),
    sa.Column('question_id', sa.Integer, nullable=False),
    sa.Column('choice_text', sa.String(200), nullable=False),
    sa.Column('votes', sa.Integer, server_default="0", nullable=False)
)





class RecordNotFound(Exception):
    """Requested record in database was not found"""
    pass


async def init_db(app):
    conf = app['config']['mysql']
    engine = await aiomysql.sa.create_engine(
        db=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
        autocommit = True,
        loop=app.loop)
    app['db'] = engine


async def close_db(app):
    app['db'].close()
    await app['db'].wait_closed()


async def get_question(conn, question_id):
    result = await conn.execute(
        question.select()
        .where(question.c.id == question_id))
    question_record = await result.first()
    if not question_record:
        msg = "Question with id: {} does not exists"
        raise RecordNotFound(msg.format(question_id))
    result = await conn.execute(
        choice.select()
        .where(choice.c.question_id == question_id)
        .order_by(choice.c.id))
    choice_recoreds = await result.fetchall()
    return question_record, choice_recoreds


async def vote(conn, question_id, choice_id):
    conn.implicit_returning = False
    upd_sql = choice.update().where(sa.and_(choice.c.question_id == question_id, choice.c.id == choice_id)).values(votes=choice.c.votes + '1')
    #print(upd_sql.compile(dialect=mysql.dialect()))
    result = await conn.execute(
        choice.update()
        .where(sa.and_(choice.c.question_id == question_id, choice.c.id == choice_id))
        .values(votes=choice.c.votes+1).execution_options(autocommit=True))

    #record = await result.fetchone()
    #if not record:
    #    msg = "Question with id: {} or choice id: {} does not exists"
    #    raise RecordNotFound(msg.format(question_id, choice_id))
