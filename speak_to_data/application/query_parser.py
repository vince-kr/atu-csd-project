import dateparser
import datetime
from spacy.tokens.doc import Doc
from speak_to_data import application


class QueryData:
    def __init__(self, raw_query: str) -> None:
        self.columns = set()
        self.docd_query: Doc = application.nlp(raw_query)
        self.crops: set[str] = self._retrieve_crops()
        self.actions: set[str] = self._retrieve_actions()
        self.locations: set[str] = self._retrieve_locations()
        self.parsed_date = QueryDatesWarnings(self.docd_query)
        self.crux: str = self._get_crux()

    def _retrieve_from_query(self, retrieve_from: set[str]) -> set[str]:
        """Generate the set of lemmas for a query and return matching action/crop"""
        query_lemmas = set(token.lemma_ for token in self.docd_query)
        intersection = retrieve_from & query_lemmas
        if "plant" in intersection:
            intersection.remove("plant")
            intersection.add("sow")
        return intersection

    def _retrieve_crops(self) -> set[str]:
        """Retrieve all crops from a given query"""
        if crops := self._retrieve_from_query(application.config.CROPS):
            self.columns.add("crop")
        return crops


    def _retrieve_actions(self) -> set[str]:
        """Retrieve all actions from a given query"""
        if actions := self._retrieve_from_query(application.config.ACTIONS):
            self.columns.add("action")
        return actions

    def _retrieve_locations(self) -> set[str]:
        if locations := self._retrieve_from_query(application.config.LOCATIONS):
            self.columns.add("location")
        return locations

    def _get_crux(self) -> str:
        quantity_indicators: tuple[str, ...] = ("how much", "how many")
        crux: str = ""
        if (
                self.docd_query[:2].text.lower() in quantity_indicators
                and self.docd_query[2].lemma_ in application.config.CROPS
        ):
            self.columns.add("quantity")
            crux = "what is sum of quantity?"
        elif ("maintenance" in set(token.lemma_ for token in self.docd_query)
              or "maintain" in set(token.lemma_ for token in self.docd_query)):
            self.columns.add("duration")
            crux = "what is sum of duration?"
        return crux

class QueryDatesWarnings:
    """Get mentions of dates out of a Doc object for use in filters"""

    def __init__(self, query: Doc) -> None:
        self.todays_date: datetime.date = datetime.date.today()
        self.date_entities = [ent.text for ent in query.ents if ent.label_ == "DATE"]
        # Generator of all date_entities that can be converted to datetime objects
        datetime_objects = (
            datetime_object
            for entity in self.date_entities
            if (datetime_object := dateparser.parse(entity))
        )
        # List of date objects that are not in the future
        self.date_objects = tuple(
            date_object
            for dto in datetime_objects
            if (date_object := dto.date()) < self.todays_date
        )

    def __bool__(self) -> bool:
        """One or two date entities in a query, all of which can be parsed"""
        one_or_two_date_entities: bool = (
            1 <= (count_date_entities := len(self.date_entities)) < 3
        )
        same_number_date_objects: bool = len(self.date_objects) == count_date_entities
        return one_or_two_date_entities and same_number_date_objects

    @property
    def _no_dates(self) -> bool:
        return len(self.date_objects) == 0

    @property
    def _one_date(self) -> bool:
        return len(self.date_objects) == 1

    @property
    def _two_dates(self) -> bool:
        return len(self.date_objects) == 2

    @property
    def date_range(self) -> tuple[datetime.date, ...]:
        """Tuple of start date, end date for filtering events"""
        if not self:
            return datetime.date.today(), datetime.date.today()

        if self._one_date:
            return self._infer_date_range(*self.date_objects)
        else:
            return self.date_objects

    def _infer_date_range(
        self, target_date: datetime.date
    ) -> tuple[datetime.date, ...]:
        days_offset: int = (self.todays_date - target_date).days
        if days_offset > 360:
            # Date range should span all of last calendar year
            last_year = self.todays_date.year - 1
            date_range = (
                datetime.date(last_year, 1, 1),
                datetime.date(last_year, 12, 31),
            )
        elif days_offset > 8:
            # Date range should span one calendar month
            year = target_date.year
            month = target_date.month
            last_day = (
                datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
            ).day
            date_range = (
                datetime.date(year, month, 1),
                datetime.date(year, month, last_day),
            )
        else:
            # Date range is about last week
            year = target_date.year
            week = target_date.isocalendar().week
            date_range = (
                datetime.date.fromisocalendar(year, week, 1),
                datetime.date.fromisocalendar(year, week, 7),
            )
        return date_range

    @property
    def warning(self) -> str:
        message = ""
        if not self.date_entities:
            message = (
                "This query does not contain any dates. "
                "Please specify a date or date range."
            )
        elif not self.date_objects:
            message = (
                f'Date reference "{self.date_entities[0]}" cannot be parsed as a date, or represents a future date.'
            )
        return message
