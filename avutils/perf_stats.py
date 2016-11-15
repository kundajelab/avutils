from collections import OrderedDict
import numpy as np

def recall_at_fdr_single_task(predicted_scores, true_y, fdr_thresholds): 
    #group by predicted prob
    from collections import defaultdict
    predicted_score_to_labels = defaultdict(list)
    for predicted_score, label in zip(predicted_scores, true_y):
        predicted_score_to_labels[predicted_score].append(label)

    #sort in ascending order of confidence
    sorted_score_thresholds = sorted(predicted_score_to_labels.keys())
    #dict mapping an fdr to the recall
    to_return_dict = OrderedDict()

    #sort the fdr thresholds in descending order
    sorted_fdr_thresholds = sorted(fdr_thresholds, key=lambda x: -x)

    total_positives = np.sum(true_y)
    total_negatives = np.sum(1-true_y)

    #start at 100% recall - everything predicted as a positive
    #first axis is true label, second axis is predicted label
    confusion_matrix_stats_so_far = [[0,total_negatives],
                                     [0,total_positives]]

    #for debugging:
    recalls_for_thresholds = []
    fdrs_for_thresholds = []

    #iterate over score thresholds in ascending order
    #that way highest recall comes first
    for threshold in sorted_score_thresholds:

        labels_at_threshold = predicted_score_to_labels[threshold]
        positives_at_threshold = sum(labels_at_threshold)
        negatives_at_threshold =\
         len(labels_at_threshold)-positives_at_threshold

        #when you cross this threshold they all get predicted as negatives.
        #move negatives_at_threshold false positives to true negatives
        confusion_matrix_stats_so_far[0][0] += negatives_at_threshold
        confusion_matrix_stats_so_far[0][1] -= negatives_at_threshold
        #move positives_at_threshold true positives to false negatives
        confusion_matrix_stats_so_far[1][1] -= positives_at_threshold
        confusion_matrix_stats_so_far[1][0] += positives_at_threshold

        #true positives + false positives is total predicted positives
        total_predicted_positives = confusion_matrix_stats_so_far[0][1]\
                                  + confusion_matrix_stats_so_far[1][1]
        #fdr = true positives / total predicted positives
        fdr = 1 - (confusion_matrix_stats_so_far[1][1]/
                   float(total_predicted_positives))\
                   if total_predicted_positives > 0 else 0.0

        #recall = true positives / total positives
        recall = confusion_matrix_stats_so_far[1][1]/float(total_positives)
        recalls_for_thresholds.append(recall)
        fdrs_for_thresholds.append(fdr)

        #once the fdr drops below one of the target thresholds,
        #record the recall and remove that threshold from the list
        while (len(sorted_fdr_thresholds) > 0
               and fdr <= sorted_fdr_thresholds[0]):
            to_return_dict[sorted_fdr_thresholds[0]] = recall
            #kick off the first entry
            sorted_fdr_thresholds = sorted_fdr_thresholds[1:]

        #break if there are no more thresholds to look for
        if len(sorted_fdr_thresholds) == 0:
            break

    #if there are any thresholds left over, record their recall as 0
    for fdr_threshold in sorted_fdr_thresholds:
        to_return_dict[fdr_threshold] = 0.0

    return to_return_dict
