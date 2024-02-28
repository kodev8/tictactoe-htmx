from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import func
from flask_login import UserMixin
from datetime import datetime

class Base(DeclarativeBase):
    pass

class PrefixBase(Base):
    __abstract__ = True
   
def prefix_table(table):
    return f'tictactoe_{table}'

db = SQLAlchemy(model_class=Base)
 
# USERS
class User(db.Model, UserMixin):

    UPDATEABLE_FIELDS = ['email', 'password', 'profile_pic']
    __tablename__ = prefix_table('users')
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    fname = mapped_column(db.String(50), nullable=False)
    lname = mapped_column(db.String(50), nullable=False)
    username = mapped_column(db.String(50), unique =True, nullable=False)
    email = mapped_column(db.String(255), unique =True, nullable=False)
    dob = mapped_column(db.Date(), nullable=False)
    password = mapped_column(db.String(255), nullable=False)
    user_since = mapped_column(db.Date(), nullable=False, default=datetime.today())
    profile_pic = mapped_column(db.String(10), nullable=True)

    pve_leaderboard = relationship('PVELeaderBoard', back_populates='user', uselist=False, cascade="all, delete", passive_deletes=True)
    pvp_leaderboard = relationship('PVPLeaderBoard', back_populates='user', uselist=False, cascade="all, delete", passive_deletes=True)

    @staticmethod
    def get_by_id(user_id):
        return db.session.scalars(db.select(User).filter_by(id=user_id)).first()
    
    @staticmethod
    def get_by_uname_or_email(username):
        username = username.lower()
        query = db.select(User).where(db.or_(User.username==username ,User.email==username))
        return  db.session.scalars(query).first()
    
    def build_path(self, folder='', filename=''):
        return f'user_{self.id}/{folder}/{filename}'
    
    def set_points(self, result, game_type):

        if game_type == 'pve':
            return self.pve_leaderboard.set_points(result)
        else:
           return self.pvp_leaderboard.set_points(result)
    
class LeaderBoard(db.Model):

    __abstract__ = True

    __tablename__ = prefix_table('leaderboard')
    user_id = mapped_column(db.Integer, db.ForeignKey(User.id), primary_key=True, autoincrement=True)
    wins = mapped_column(db.Integer, default=0, nullable=False)
    draws = mapped_column(db.Integer, default=0, nullable=False)
    losses = mapped_column(db.Integer, default=0, nullable=False)
    points = mapped_column(db.Integer, default=0, nullable=False)

    def dense_rank_query(self):
        query = db.select(  
                            func.dense_rank().over(
                            order_by=( 
                                self.__class__.points.desc(), 
                                self.__class__.wins.desc(),
                                (self.__class__.wins + self.__class__.losses + self.__class__.draws).label('total_games')
                            )).label('dense_rank'),
                            self.__class__,
                            )
        return query
    
    def get_dense_rank(self, top: int = 20): # Returns array of rank, LeaderBoard obj
        """Returns the top 20 players in the leaderboard or if with user parameter, the user's rank"""
        query = self.dense_rank_query()
        return  db.session.execute(query.order_by(self.__class__.points.desc()).limit(top)).all()
    
    @classmethod
    def reset_leaderboard(cls):
        """Resets the leaderboard"""
        # check for all users to ensure that they have a leaderboard entry
        users = db.session.execute(db.select(User.id)).all()
        for user in users:
            db.session.add(cls(user_id=user.id))

        db.session.execute(db.update(cls).values(wins=0, draws=0, losses=0, points=0))
        db.session.commit()

    def set_points(self, result):
        if result == 'w':
            self.wins += 1
        elif result == 'd':
            self.draws += 1
        else:
            self.losses += 1

        self.points = self.calcultate_points()
        db.session.commit()

        return self.POINTS.get(result)

        

    def calcultate_points(self):
        return self.POINTS['w'] * self.wins + self.POINTS['d'] * self.draws
    
    def get_user_rank(self):
        """Concrete implementation for user rank: Returns the user's rank"""
        query = self.dense_rank_query() # should now be a subquery
        query= db.select(query.c.dense_rank).where(query.c.user_id == self.user.id)
        return db.session.execute(query).first()[0]
    
class PVELeaderBoard(LeaderBoard):
    __tablename__ = prefix_table('pve_leaderboard')

    # TODO: Add points per game mode
    POINTS = {
        'w': 30,
        'd':10,
        'l': 0 # stated for clarity
    }

    user = relationship('User', back_populates='pve_leaderboard', uselist=False)

class PVPLeaderBoard(LeaderBoard):
    __tablename__ = prefix_table('pvp_leaderboard')
    POINTS = {
        'w': 50,
        'd':20,
        'l': 0
    }
    user = relationship('User', back_populates='pvp_leaderboard', uselist=False)


    # SELECT id, points,
    # dense_rank() OVER (ORDER BY points DESC, wins DESC, (wins + losses + draws) DESC) AS dr
    # FROM leader_board
    # ORDER BY points DESC;
    