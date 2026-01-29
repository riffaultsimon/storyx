from db.session import SessionLocal
from db.models import User                                                                                                                                                   

db = SessionLocal()
user = db.query(User).filter(User.email == 'riffaultsimon@gmail.com').first()
if user:
    user.is_admin = True
    db.commit()
    print(f'{user.username} is now admin')
else:
    print('User not found')
db.close()