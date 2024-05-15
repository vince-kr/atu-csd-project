from flask_wtf import FlaskForm


class ActionForm(FlaskForm):
    def get_type_of_action(self) -> str:
        return type(self).__name__[:-4].lower()
