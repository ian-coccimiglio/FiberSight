---
name:
author:
title:
date:

---

# Assessment of Fiber-Typing protocol

Muscle fiber type assessment from immunofluorescence data is predicated on the following structure.
1) Accurately segmenting muscle fibers from a cross-sectional slice.
2) Artifact correction and normalization of the underlying fluorescence signal
3) Classification of a fiber type.

The first step - fiber segmentation - can be handled by a modern well-trained image segmentation model.

However, steps 2 and 3 both require additional justification and specification, in order to obtain our central goal, stated below.

We wish to obtain a reproducible classification of muscle fiber types, such that the assigned fiber-type frequencies are dependent only on the selected thresholds, and such that the differences between-samples is primarily characterized by differences in the biological signal.

By example, the following might be an output from a fiber-type analysis of one sample.
- 30% of fibers are Type I
- 40% of fibers are Type IIa
- 30% of fibers are UND-

The model stipulates that you must choose pre-defined thresholds prior to fiber type classification. However, the model does not state what in particular these thresholds should be.

However, between-samples, these thresholds are fixed. The sample-to-sample variation is therefore independent of the threshold. So instead, the distribution of fiber-types will have a mean and standard deviation about a particular value.

If a secondary condition is added, these means and standard deviations may vary between conditions, and since these samples are independent and their output values are pseudo-continuous, the difference can be statistically assessed using a classical two samples T-Test. The result of that test is conditional on the model, and the power of the model is conditional on the choice of thresholds accurately reflecting the true distribution of fiber-types.

Important to note, the result of adding more stains can change these proportions.
