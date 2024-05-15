import dataclasses
import dateparser
import datetime
from spacy.tokens.doc import Doc
from speak_to_data import application


select_columns = set()


def _retrieve_from_query(query: Doc, retrieve_from: set[str]) -> set[str]:
    """Generate the set of lemmas for a given query and return matching action/crop"""
    query_lemmas = set(token.lemma_ for token in query)
    intersection = retrieve_from & query_lemmas
    if "plant" in intersection:
        intersection.remove("plant")
        intersection.add("sow")
    return intersection


def retrieve_crop(query: Doc) -> set[str]:
    """Retrieve all crops from a given query"""
    if crops := _retrieve_from_query(query, application.config.CROPS):
        select_columns.add("crop")
    return crops


def retrieve_action(query: Doc) -> set[str]:
    """Retrieve all actions from a given query"""
    if actions := _retrieve_from_query(query, application.config.ACTIONS):
        select_columns.add("action")
    return actions


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

    @staticmethod
    def _compute_date_range(
        start: datetime.date, end: datetime.date
    ) -> tuple[datetime.date, datetime.date]:
        return start, end

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
                f'Date reference "{self.date_entities[0]}" cannot be parsed '
                f"as a date, or represents a future date."
            )
        return message


def get_crux(query: Doc) -> str:
    quantity_indicators: tuple[str, ...] = ("how much", "how many")
    crux: str = ""
    if (
        query[:2].text.lower() in quantity_indicators
        and query[2].lemma_ in application.config.CROPS
    ):
        select_columns.add("quantity")
        crux = "what is sum of quantity?"
    return crux


@dataclasses.dataclass
class QueryData:
    docd_query: Doc
    action: set[str]
    crop: set[str]
    query_dates: QueryDatesWarnings
    crux: str
    columns: set[str]

    def __bool__(self) -> bool:
        return bool(self.crux and self.query_dates)


def parse_query(raw_user_query: str) -> QueryData:
    docd_query: Doc = application.nlp(raw_user_query)
    return QueryData(
        docd_query=docd_query,
        action=retrieve_action(docd_query),
        crop=retrieve_crop(docd_query),
        query_dates=QueryDatesWarnings(docd_query),
        crux=get_crux(docd_query),
        columns=select_columns,
    )
