class PricingError(Exception):
    """Base class for all errors in price calculator."""

class IndexBandNotFound(PricingError):
    """No index range found for the given year, type, and percentage."""

    def __init__(self, pricing_year, index_type, percent):
        self.pricing_year = pricing_year
        self.index_type = index_type
        self.percent = percent
        super().__init__(
            f'Missing index for year {pricing_year}, '
            f'Type "{index_type}" & percent {percent}.'
        )

class MissingPriceError(PricingError):
    """Missing base price for given target group for give year."""

    def __init__(self, pricing_year, target_group):
        self.pricing_year = pricing_year
        self.target_group = target_group
        super().__init__(
            f'No base price for target group "{target_group}" for {pricing_year} year.'
        )


class MissingCoefficientError(PricingError):
    """Missing monthly coefficient for given year and month."""

    def __init__(self, pricing_year, month):
        self.pricing_year = pricing_year
        self.month = month
        super().__init__(
            f'No monthly coefficient for month {month} for {pricing_year} year.'
        )

class InvalidPercentError(PricingError):
    """A percentage is outside the allowed 0-100 range."""

    def __init__(self, name, percent):
        self.name = name
        self.percent = percent
        super().__init__(f'{name} must be between 0 and 100, got {percent}.')
