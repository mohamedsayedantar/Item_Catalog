from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_create import Categories, Base, Items, User

engine = create_engine('sqlite:///categories.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

category1 = Categories(name="Soccer")
session.add(category1)
session.commit()
item1 = Items(name="Jersey",
              description="any description can be written here",
              categories=category1)
session.add(item1)
session.commit()
item2 = Items(name="Soccer Cleats",
              description="any description can be written here",
              categories=category1)
session.add(item2)
session.commit()

category2 = Categories(name="Basketball")
session.add(category2)
session.commit()
item1 = Items(name="Bat", description="any description can be written here",
              categories=category2)
session.add(item1)
session.commit()

category3 = Categories(name="Baseball")
session.add(category3)
session.commit()

category4 = Categories(name="Frisbee")
session.add(category4)
session.commit()

category5 = Categories(name="Snowboarding")
session.add(category5)
session.commit()

category6 = Categories(name="Rock Climbing")
session.add(category6)
session.commit()

category7 = Categories(name="Foosball")
session.add(category7)
session.commit()

category8 = Categories(name="Skating")
session.add(category8)
session.commit()

category9 = Categories(name="Hokey")
session.add(category9)
session.commit()

print "the categories added successfully"
