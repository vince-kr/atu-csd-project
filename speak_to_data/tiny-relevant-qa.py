from transformers import TapasTokenizer, TapasForQuestionAnswering
import pandas as pd

# Set up the model
model_name = "google/tapas-large-finetuned-wtq"
model = TapasForQuestionAnswering.from_pretrained(model_name)
tokenizer = TapasTokenizer.from_pretrained(model_name)

# Sample data
data = {
    # Working example of a simple table with monthly totals
    "year": ["2024", "2024", "2024"],
    "month": ["February", "March", "April"],
    "how_many": ["120", "190", "202"]
}

"""
data = {
    # The below table does not result in accurate results
    "year": ["2024", "2024", "2024", "2024", "2024", "2024"],
    "month": ["March", "March", "March", "March", "March", "April"],
    "day": ["1", "4", "12", "20", "28", "6"],
    "how_many": ["8", "4", "6", "5", "7", "9"],
}
"""

queries = [
    "How many eggs were gathered in March?",
    "How many eggs were gathered in 2024?",
]

table = pd.DataFrame.from_dict(data)
inputs = tokenizer(table=table, queries=queries,
                   padding="max_length", return_tensors="pt")
outputs = model(**inputs)
predicted_answer_coordinates, predicted_aggregation_indices = (
    tokenizer.convert_logits_to_predictions(
        inputs, outputs.logits.detach(), outputs.logits_aggregation.detach()
    )
)

id2aggregation = {0: "NONE", 1: "SUM", 2: "AVERAGE", 3: "COUNT"}
aggregation_predictions_string = [id2aggregation[x] for x in predicted_aggregation_indices]

answers = []
for coordinates in predicted_answer_coordinates:
    if len(coordinates) == 1:
        # only a single cell:
        answers.append(table.iat[coordinates[0]])
    else:
        # multiple cells
        cell_values = []
        for coordinate in coordinates:
            cell_values.append(table.iat[coordinate])
        answers.append(", ".join(cell_values))

for query, answer, predicted_agg in zip(queries, answers, aggregation_predictions_string):
    print(query)
    if predicted_agg == "NONE":
        print("Predicted answer: " + answer)
    else:
        print("Predicted answer: " + predicted_agg + " > " + answer)
