(function (root, factory) {
  const api = factory();

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.SignSpeakModel = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  function predict(features, model) {
    if (!Array.isArray(features) || features.length !== model.n_features) {
      throw new Error('Incorrect number of input features.');
    }

    if (!features.every(Number.isFinite)) {
      throw new Error('Features must all be finite numbers.');
    }

    const probabilities = new Array(model.classes.length).fill(0);

    for (const tree of model.trees) {
      let node = 0;

      while (tree.left[node] !== -1) {
        const featureIndex = tree.feature[node];

        if (features[featureIndex] <= tree.threshold[node]) {
          node = tree.left[node];
        } else {
          node = tree.right[node];
        }
      }

      const leafProbabilities = tree.leaf_values[node];

      for (let i = 0; i < probabilities.length; i++) {
        probabilities[i] += leafProbabilities[i];
      }
    }

    for (let i = 0; i < probabilities.length; i++) {
      probabilities[i] /= model.n_trees;
    }

    let bestIndex = 0;

    for (let i = 1; i < probabilities.length; i++) {
      if (probabilities[i] > probabilities[bestIndex]) {
        bestIndex = i;
      }
    }

    return {
      letter: model.classes[bestIndex],
      confidence: probabilities[bestIndex],
      probabilities: probabilities,
    };
  }

  return { predict: predict };
});
