const fs = require("fs");
require("../static/js/model.js");
const modelPredictor = globalThis.SignSpeakModel;

const model = JSON.parse(
    fs.readFileSync("static/models/sign_model.json", "utf8")
);

const testCases = JSON.parse(
    fs.readFileSync("data/model_test_cases.json", "utf8")
);

let predictionMismatches = 0;
let probabilityMismatches = 0;
let maximumDifference = 0;

const tolerance = 1e-10;

for (let index = 0; index < testCases.length; index++) {
    const testCase = testCases[index];

    const result = modelPredictor.predict(testCase.features, model);

    if (result.letter !== testCase.expected_prediction) {
        predictionMismatches++;
        console.log(
            "Prediction mismatch:",
            testCase.label,
            "Expected:",
            testCase.expected_prediction,
            "Got:",
            result.letter
        );
    }

    for (let i = 0; i < result.probabilities.length; i++) {
        const difference = Math.abs(
            result.probabilities[i] -
            testCase.expected_probabilities[i]
        );

        maximumDifference = Math.max(maximumDifference, difference);

        if (difference > tolerance) {
            probabilityMismatches++;
        }
    }
}

console.log("\n===== JavaScript vs Python Model Test =====");
console.log("Test cases:", testCases.length);
console.log("Trees:", model.n_trees);
console.log("Classes:", model.classes.length);
console.log("Features:", model.n_features);
console.log("Prediction mismatches:", predictionMismatches);
console.log("Probability mismatches:", probabilityMismatches);
console.log("Maximum probability difference:", maximumDifference);
console.log(
    "Result:",
    predictionMismatches === 0 && probabilityMismatches === 0
        ? "ALL TESTS PASSED"
        : "TESTS FAILED"
);

if (predictionMismatches !== 0 || probabilityMismatches !== 0) {
    process.exitCode = 1;
}

