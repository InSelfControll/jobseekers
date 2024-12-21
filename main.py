
import os
from app import create_app
from extensions import socketio, db, migrate
from bot.telegram_bot import start_bot
from flask_migrate import Migrate, upgrade

def main():
    app = create_app()
    
    # Initialize migrations with app and db
    migrate.init_app(app, db)
    
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Initialize migrations directory if it doesn't exist
            if not os.path.exists('migrations'):
                print("Initializing migrations directory...")
                os.system('flask db init')
            
            try:
                print("Creating migration for current model changes...")
                os.system('flask db migrate -m "Update database schema"')
                
                print("Applying migrations...")
                upgrade()
            except Exception as e:
                print(f"Migration error (this may be normal for first run): {e}")
                
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=3000, debug=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Received keyboard interrupt")
    except Exception as e:
        print(f"Fatal error: {e}")
