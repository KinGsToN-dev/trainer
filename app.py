from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = 'super_secret_trainer_key'

    # Регистрируем Blueprints (чертежи)
    from blueprints.main import main_bp
    from blueprints.learning import learning_bp
    from blueprints.sandbox import sandbox_bp
    from blueprints.management import management_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(sandbox_bp)
    app.register_blueprint(management_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
