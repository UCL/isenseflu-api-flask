from app import db


class FluModel(db.Model):

    __tablename__ = 'model'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    source_type = db.Column(db.Text, nullable=False)
    is_public = db.Column(db.Boolean, nullable=False)
    is_displayed = db.Column(db.Boolean, nullable=False)
    calculation_parameters = db.Column(db.Text, nullable=True)
    model_scores = db.relationship('ModelScore')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get_model_parameters(self):
        """Parse this model's data attribute and return a dict"""
        if self.source_type in ['google', 'twitter']:
            matlab_function, average_window_size = self.calculation_parameters.split(',')
            return {
                'matlab_function': matlab_function,
                'average_window_size': int(average_window_size)
            }

    @staticmethod
    def get_all_public():
        return FluModel.query.filter_by(is_public=True).all()

    @staticmethod
    def get_model_for_id(id):
        return FluModel.query.filter_by(id=id).first()

    def __repr__(self):
        return '<Model %s>' % self.name


class ModelScore(db.Model):

    calculation_timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    score_date = db.Column(db.Date, primary_key=True)
    region = db.Column(db.Text, primary_key=True)
    score_value = db.Column(db.Float, nullable=False)

    flu_model_id = db.Column(db.Integer, db.ForeignKey('model.id'), primary_key=True)

    @staticmethod
    def get_scores_for_dates(model_id, start_date, end_date):
        return ModelScore.query.filter(
            ModelScore.flu_model_id==model_id,
            ModelScore.score_date>=start_date,
            ModelScore.score_date<=end_date
        ).all()

    def __repr__(self):
        return '<ModelScore %s %s %f>' % (
            self.day.strftime('%Y-%m-%d'), self.region, self.value)


class GoogleScore(db.Model):

    retrieval_timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    score_date = db.Column(db.Date, primary_key=True)
    score_value = db.Column(db.Float, nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('google_term.id'), primary_key=True)

    def __repr__(self):
        return '<GoogleScore %s %f>' % (
            self.day.strftime('%Y-%m-%d'), self.value)


class GoogleTerm(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.Text, unique=True, index=True, nullable=False)

    def __repr__(self):
        return '<GoogleTerm %s>' % self.term
