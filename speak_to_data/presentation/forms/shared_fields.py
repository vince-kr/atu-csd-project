import datetime

from speak_to_data import application
from wtforms import DateField, SelectField, StringField
from wtforms.validators import AnyOf, Length
from wtforms_components import DateRange

app_data_loader = application.AppDataLoader(application.config.APP_DATA_PATH)

all_crops = app_data_loader.load_crops()
crop = SelectField(
    "Crop",
    validate_choice=False,
    validators=[
        AnyOf(
            values=tuple(lt[0] for lt in all_crops),
            message=f"Not a valid choice.\n{application.config.NOT_SAVED_WARNING}",
        )
    ],
    choices=all_crops,
)

quantity = StringField(label="Quantity", validators=[Length(max=255)])

all_locations = app_data_loader.load_locations()
location = SelectField("Location", choices=all_locations)

all_location_types = app_data_loader.load_location_types()
location_type = SelectField(
    "Location type",
    validators=[
        AnyOf(
            values=tuple(lt[0] for lt in all_location_types),
            message=f"Not a valid choice.\n{application.config.NOT_SAVED_WARNING}",
        )
    ],
    choices=all_location_types,
)

date = DateField(
    validators=[
        DateRange(
            max=datetime.date.today(),
            message=f"Event date cannot be in the future.\n"
            f"{application.config.NOT_SAVED_WARNING}",
        )
    ]
)
