"""
Data model used by the app (SQLAlchemy is used as ORM)
"""

from datetime import date, timedelta

from app import DB


class FluModel(DB.Model):
    """
    ORM Model representing a Flu Model
    """

    __tablename__ = 'model'

    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String, unique=True, nullable=False)
    source_type = DB.Column(DB.Text, nullable=False)
    is_public = DB.Column(DB.Boolean, nullable=False)
    is_displayed = DB.Column(DB.Boolean, nullable=False)
    calculation_parameters = DB.Column(DB.Text, nullable=True)
    model_region_id = DB.Column(DB.Text, nullable=True)
    model_scores = DB.relationship('ModelScore')
    model_function = DB.relationship('ModelFunction')

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def delete(self):
        """ Convenience method to delete current instance """
        DB.session.delete(self)
        DB.session.commit()

    def get_model_parameters(self):
        """Parse this model's data attribute and return a dict"""
        if self.source_type in ['google', 'twitter']:
            matlab_function, average_window_size = self.calculation_parameters.split(',')
            return {
                'matlab_function': matlab_function,
                'average_window_size': int(average_window_size)
            }
        return None

    def __repr__(self):
        return '<Model %s>' % self.name


class DefaultFluModel(DB.Model):
    """
    ORM Model to define the default public model to be returned by the API
    """

    id = DB.Column(DB.Integer, primary_key=True)
    flu_model_id = DB.Column(DB.Integer, DB.ForeignKey('model.id'))

    def __repr__(self):
        return '<DefaultFluModel %d>' % self.flu_model_id


class ModelFunction(DB.Model):
    """
    ORM Model to define the function used to calculate the model scores
    """

    id = DB.Column(DB.Integer, primary_key=True)
    function_name = DB.Column(DB.String, nullable=False)
    average_window_size = DB.Column(DB.Integer, nullable=False)
    has_confidence_interval = DB.Column(DB.Boolean)

    flu_model_id = DB.Column(DB.Integer, DB.ForeignKey('model.id'))

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()


class ModelScore(DB.Model):
    """
    ORM Model representing a data point of a model score
    """

    calculation_timestamp = DB.Column(DB.DateTime, default=DB.func.current_timestamp())
    score_date = DB.Column(DB.Date, primary_key=True)
    region = DB.Column(DB.Text, primary_key=True)
    score_value = DB.Column(DB.Float, nullable=False)
    confidence_interval_lower = DB.Column(DB.Float, nullable=True)
    confidence_interval_upper = DB.Column(DB.Float, nullable=True)

    flu_model_id = DB.Column(DB.Integer, DB.ForeignKey('model.id'), primary_key=True)

    def moving_avg(self, days):
        """ Calculate moving average over a window of days """
        window = timedelta(days=max(0, (days - 1) / 2))
        scores = ModelScore.query.filter(
            ModelScore.flu_model_id == self.flu_model_id,
            ModelScore.score_date >= self.score_date - window,
            ModelScore.score_date <= self.score_date + window,
            ModelScore.region == self.region).all()
        avg_score = sum(s.score_value for s in scores) / len(scores)
        avg_upper_conf = sum(
            s.confidence_interval_upper for s in scores if s.confidence_interval_upper is not None
        ) / len(scores)
        avg_lower_conf = sum(
            s.confidence_interval_lower for s in scores if s.confidence_interval_lower is not None
        ) / len(scores)
        return avg_score, avg_upper_conf, avg_lower_conf

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def __repr__(self):
        return '<ModelScore %s %s %f>' % (
            self.score_date.strftime('%Y-%m-%d'), self.region, self.score_value)


class GoogleScore(DB.Model):
    """
    ORM Model representing a data point of a score retrieved from Google Health Trends private API
    """

    retrieval_timestamp = DB.Column(DB.DateTime, default=DB.func.current_timestamp())
    score_date = DB.Column(DB.Date, primary_key=True)
    term_id = DB.Column(DB.Integer, DB.ForeignKey('google_term.id'), primary_key=True)
    score_value = DB.Column(DB.Float, nullable=False)

    def __init__(self, term_id: int, score_date: date, score_value: float):
        self.term_id = term_id
        self.score_date = score_date
        self.score_value = score_value

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def __repr__(self):
        return '<GoogleScore term_id=%d %f>' % (self.term_id, self.value)


class GoogleTerm(DB.Model):
    """
    ORM Model representing a term used in querying Google Health Trends API
    """

    id = DB.Column(DB.Integer, primary_key=True)
    term = DB.Column(DB.Text, unique=True, index=True, nullable=False)

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def __repr__(self):
        return '<GoogleTerm %s>' % self.term


class GoogleDate(DB.Model):
    """
    ORM Model representing the date for which a complete set of Google terms for a particular model
    ID was retrieved. The date here stored assumes the scores for a set of Google terms as a
    transaction and should always be added to the session together with the set of GoogleScores.
    """

    id = DB.Column(DB.Integer, primary_key=True)
    flu_model_id = DB.Column(DB.Integer, DB.ForeignKey('model.id'))
    transaction_timestamp = DB.Column(DB.DateTime, default=DB.func.current_timestamp())
    score_date = DB.Column(DB.Date)

    def __init__(self, model_id: int, score_date: date):
        self.flu_model_id = model_id
        self.score_date = score_date

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def __repr__(self):
        return '<GoogleDate model_id=%d %s>' % (
            self.flu_model_id, self.score_date.strftime('%Y-%m-%d')
        )


class FluModelGoogleTerm(DB.Model):
    """
    ORM Model representing a link table between FluModel and GoogleTerm
    """

    flu_model_id = DB.Column(DB.Integer, DB.ForeignKey('model.id'), primary_key=True)
    google_term_id = DB.Column(DB.Integer, DB.ForeignKey('google_term.id'), primary_key=True)

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()


class RateThresholdSet(DB.Model):
    """
    ORM Model representing the list of current set of epidemic rate thresholds as published by PHE
    """

    threshold_set_id = DB.Column(DB.Integer, primary_key=True)
    log_timestamp = DB.Column(DB.DateTime, default=DB.func.current_timestamp())
    low_value = DB.Column(DB.Float)
    medium_value = DB.Column(DB.Float)
    high_value = DB.Column(DB.Float)
    very_high_value = DB.Column(DB.Float)
    valid_from = DB.Column(DB.Date)
    valid_until = DB.Column(DB.Date)

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()


class TokenInfo(DB.Model):
    """
    ORM Model representing a set of tokens
    """

    token_id = DB.Column(DB.Integer, primary_key=True)
    token = DB.Column(DB.Text, nullable=False)
    token_user = DB.Column(DB.Text, nullable=False)
    is_valid = DB.Column(DB.Boolean, default=False)

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()
