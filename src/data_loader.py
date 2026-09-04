import pandas as pd


class Dataloader:

    def __init__(self, file_path):
        self.file_path = file_path


    def load_csv(self):

        print("\nLoading CSV file...")

        df = pd.read_csv(
            self.file_path,
            encoding="utf-8-sig"
        )

        print("CSV loaded successfully.")
        print("Total Records:", len(df))

        return df