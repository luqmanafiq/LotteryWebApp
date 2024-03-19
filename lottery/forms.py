from flask import flash
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField


class DrawForm(FlaskForm):
    number1 = IntegerField(id='no1')
    number2 = IntegerField(id='no2')
    number3 = IntegerField(id='no3')
    number4 = IntegerField(id='no4')
    number5 = IntegerField(id='no5')
    number6 = IntegerField(id='no6')
    submit = SubmitField("Submit Draw")

    def validate(self, **kwargs):
        standard_validators = FlaskForm.validate(self)
        if standard_validators:
            numbers = [
                self.number1.data,
                self.number2.data,
                self.number3.data,
                self.number4.data,
                self.number5.data,
                self.number6.data,
            ]

            if len(set(numbers)) != len(numbers):
                flash('All numbers must be unique. ')
                return False

        return standard_validators
