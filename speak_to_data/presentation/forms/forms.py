from speak_to_data import application
from speak_to_data.presentation.forms import action_form, shared_fields
from wtforms import RadioField, StringField
from wtforms.validators import AnyOf


class QueryForm(action_form.ActionForm):
    user_query = StringField("User query")


class SowForm(action_form.ActionForm):
    date = shared_fields.date
    crop = shared_fields.crop
    quantity = shared_fields.quantity
    location = shared_fields.location
    location_type = shared_fields.location_type


class MaintainForm(action_form.ActionForm):
    date = shared_fields.date
    duration = RadioField(
        validate_choice=False,
        validators=[
            AnyOf(
                values=("1", "3", "6"),
                message=f"Not a valid choice.\n{application.config.NOT_SAVED_WARNING}",
            )
        ],
        choices=(
            ("1", "Less than 30 minutes"),
            ("3", "Between 30 and 90 minutes"),
            ("6", "More than 90 minutes"),
        ),
    )
    location = shared_fields.location
    location_type = shared_fields.location_type


class HarvestForm(action_form.ActionForm):
    date = shared_fields.date
    crop = shared_fields.crop
    quantity = shared_fields.quantity
    location = shared_fields.location
    location_type = shared_fields.location_type
