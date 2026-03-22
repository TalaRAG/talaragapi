class Validator:
    def __init__(self):
        self.payload = {}
        self.num_errors = 0

    def valid(self):
        return self.num_errors == 0

    def invalid(self):
        return self.num_errors > 0

    def count_errors(self):
        self.num_errors = 0
        for errors in self.payload.values():
            if not errors:
                continue

            first = errors[0]
            if isinstance(first, str):
                self.num_errors += len(errors)
                continue

            if isinstance(first, dict):
                for entry in errors:
                    if not entry:
                        continue
                    for nested_errors in entry.values():
                        if nested_errors:
                            self.num_errors += len(nested_errors)
