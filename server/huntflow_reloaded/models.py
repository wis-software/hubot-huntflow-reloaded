""" Database GINO models """

# pylint: disable=maybe-no-member

from gino.ext.tornado import Gino

DB = Gino()

class Candidate(DB.Model):
    """ Candidate for vacancy model """

    __tablename__ = 'Candidates'

    id = DB.Column(DB.Integer())

    first_name = DB.Column(DB.String())
    last_name = DB.Column(DB.String())

    __table_args__ = (DB.UniqueConstraint('id'))

class Inerview(DB.Model):
    """ Interview event model """

    __tablename__ = 'Inerviews'

    id = DB.Column(DB.Integer(), primary_key=True, autoincrement=True)

    created = DB.Column(DB.DateTime())
    type = DB.Column(DB.String())

    candidate = DB.Column(DB.Integer(), DB.ForeignKey('Candidates.id'))

    start = DB.Column(DB.DateTime())
    end = DB.Column(DB.DateTime())

    __table_args__ = (DB.UniqueConstraint('id'))

async def gino_run(**kwargs):
    """ Connecting to the database and creating models """

    postgres_url = 'postgresql://%(username)s:%(password)s@%(hostname)s/%(dbname)s'

    await DB.set_bind(postgres_url % kwargs)
