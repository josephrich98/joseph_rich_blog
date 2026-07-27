---
title: "Radiology AI Is Not Computer Vision: A Field Guide for ML Scientists"
author: "Joseph Rich"
date: "2026-06-02"
bibliography: references.bib
csl: ../../templates/csl/american-medical-association.csl
link-citations: true
reference-section-title: References
# Blog metadata (ignored by pandoc/Eisvogel; consumed by scripts/sync_posts.py)
excerpt: "A field guide for ML scientists working in radiology imaging. How is radiology similar to standard computer vision, and how is it different? This post covers a radiology primer, some medical context that makes radiology data different from standard imaging, some widely-used radiology datasets, and some popular radiology AI models."
tags:
  - machine learning
  - radiology
  - computer vision
  - medical imaging
titlepage: true
toc: true
toc-own-page: true
colorlinks: true
linkcolor: NavyBlue
urlcolor: NavyBlue
listings: true
---

## Radiology primer
Radiology is the medical specialty that uses imaging to diagnose and treat disease. Radiological imaging allows for visualization of entire tissues or organs in the body, which differentiates radiology from cellular-based imaging that is common in genomics and pathology. The most common causes for radiology imaging trauma and injuries (broken bones, internal bleeding), cancer (tumor detection, staging, and monitoring), and chronic diseases (heart disease, liver disease, lung disease). 

Images are organized heirarchically. Each 2D image is called a slice, and a series of slices can be stacked to form a 3D volume, or a series. A study is comprised of one or more series, and a patient can have multiple studies. For instance, a patient may have a chest CT study with two series: one without contrast and one with contrast. One patient can have multiple studies over time, such as a chest CT study in 2020 and a follow-up chest CT study in 2022.

The most common modalities are X-ray, CT, MRI, ultrasound, and nuclear medicine (PET/SPECT). X-ray and CT use ionizing radiation to produce images. The more signal a tissue blocks, the whiter it appears on the image. X-rays are commonly used for bone and chest imaging. A CT scan is a series of X-ray images taken from different angles and reconstructed into a 3D volume. There are three possible slice orientations: axial (top-down), coronal (front-back), and sagittal (side). CT is commonly used for chest, abdominal, and brain imaging. MRI uses magnetic fields and radio waves (the same technology as proton nuclear magnetic resonance), also capturing 3D volumes. MRI enables soft tissue visualization in higher detail compared to CT, and has the advantage of not using ionizing radiation. Ultrasound uses high-frequency sound waves, and is commonly used for obstetrics, cardiology, and abdominal imaging. Nuclear medicine uses radioactive tracers to visualize physiological processes, used in diagnostic procedures such as studying brain activity and thyroid function.

![**Figure 1**](figures/imaging_modalities.png)

**Figure 1**: Imaging modalities. Made with ChatGPT.

## Radiology and computer vision similarities and differences
Let me blow your mind: radiology images are a type of image. They're a grid of pixels, just like any other image, even if it is less visually stimulating to look at a picture of lung opacities than a picture of a dog. This means that all the same computer vision architectures that work on natural images can be applied to radiology images.

<table>
  <tr>
    <td align="center">
      <img src="figures/lung.jpg" height="240"><br>
      <span style="font-style: normal;">Picture of lung opacities.</span><br>
      <small style="color: gray;">
        Source:
        <a href="https://radiologyassistant.nl/chest/chest-x-ray/lung-disease">
          Radiology Assistant
        </a>
      </small>
    </td>
    <td align="center">
      <img src="figures/dog_in_suit.jpeg" height="240"><br>
      <span style="font-style: normal;">Picture of a dog in a suit.</span><br>
      <small style="color: gray;">
        Source:
        <a href="https://www.amazon.com/Rubies-unisex-Business-Costume-Multicolor/dp/B01C4K8334">
          Rubies
        </a>
      </small>
    </td>
  </tr>
</table>

However, there are some important differences between radiology and natural images that make radiology a unique domain for machine learning.

### Annotation requires domain expertise

It takes substantial medical training even to recognize the anatomy in a radiology image, let alone to identify pathology. Patients can have substantial variability in their anatomy, which can make it dfficult to discern disease from normal variation. Tumors can come in all shapes and sizes, sometimes making them difficult to identify from surrounding tissue, cysts, or other benign findings. Some diseases have highly characteristic imaging appearances—for example, the boot-shaped heart of tetralogy of Fallot or the coffee bean sign of sigmoid volvulus. However, many diseases exhibit substantial variability across patients. For instance, pneumonia may appear as focal lobar consolidation, patchy multifocal opacities, diffuse interstitial infiltrates, or even be nearly occult on early imaging. This diversity makes medical image interpretation a challenging pattern-recognition task.

### Most pixels are uninformative; a few pixels can make the difference
In many computer vision tasks, the object of interest occupies a significant portion of the image. Think of a digit in an MNIST image, or a cat in a COCO image. In these cases, the object is large enough that it can be easily detected and classified by a model. In radiology, however, the finding is often a small fraction of the image, and the difference between a benign and malignant finding can be subtle. For example, a small pulmonary nodule may only occupy a few pixels in a CT scan, but its presence or absence can have significant clinical implications.

![**Figure 1**](figures/needle_in_haystack.png)

**Figure 1**: The fraction of an image that actually belongs to the finding,
on a log scale. Natural-image objects (blue) occupy $10^{-3}$ to $10^{0}$ of the
frame. Clinically critical lesions (red/navy) sit at $10^{-7}$ to $10^{-5}$.
This five-to-six order-of-magnitude difference is why naive pixel-wise losses
and patch samplers fail in radiology.

As a concrete example, let's consider a chest CT scan. A chest CT of roughly $512 \times 512 \times 320$ voxels at $0.7 \times 0.7 \times 1.0\,\text{mm}$ contains about $8.4 \times 10^7$
voxels. A clinically important $5\,\text{mm}$ pulmonary nodule is a sphere of
volume $\tfrac{4}{3}\pi r^3 \approx 65\,\text{mm}^3$, or about $134$ voxels. The
lesion is therefore
$$
\frac{134}{8.4\times 10^7} \approx 1.6 \times 10^{-6}
$$
of the volume — roughly one in six hundred thousand voxels. Figure 1 puts
several findings on the same axis as natural-image objects; note the five-to-six
order-of-magnitude gap.

This gap means that pixelwise accuracy is a poor metric for evaluating segmentation model performance. A segmentation model that predicts "no lesion" everywhere achieves $1 - 1.6\times10^{-6} \approx 99.9998\%$ voxel accuracy. Use overlap and detection metrics built for imbalance — Dice / $F_1$, where for prediction $P$ and ground truth $G$, $$\mathrm{Dice} = \frac{2|P \cap G|}{|P| + |G|},$$ free-response ROC (FROC) for detection, and class-balanced or region-based losses (Dice loss, Tversky, focal). The focal loss down-weights the easy negatives that otherwise dominate the gradient: $\mathrm{FL}(p_t) = -(1-p_t)^{\gamma}\log p_t$.

This gap also means that image preprocessing may be necessary before passing through a model. Masking out uninformative regions of the image, such as the background or areas of normal tissue, can help the model focus on the relevant regions. Additionally, using multi-scale approaches or attention mechanisms can help the model capture small lesions that may be missed at a single scale.

### Data are often scarce and heterogeneous
Natural-image research has access to a wealth of images. ImageNet has 1.4 million images, InfiMNIST can generate effectively infinite images, and webscale datasets have billions of images. Radiology has a few public datasets with over 10,000 images, generally for chest x-ray and/or healthy patients, but most datasets are much smaller. As soon as one focuses on a particular disease, modality, or patient population, they will be hard-pressed to find more than a few hundred images. A few of the most popular public datasets are summarized in Table 1.

| Dataset | Modality | Scale | Notes | Ref. |
| --- | --- | --- | --- | --- |
| **TCIA** (The Cancer Imaging Archive) | CT/MR/PET, many | Umbrella of 100+ collections | The host for most public oncology imaging, incl. LIDC-IDRI, BraTS sources |[@clark2013] |
| **MIMIC-CXR** | Chest X-ray | 377,110 images / 227,835 studies / 65,379 patients | Single US center; paired free-text reports |[@johnson2019] |
| **CheXpert** | Chest X-ray | 224,316 images / 65,240 patients | Stanford; 14 NLP-mined labels with uncertainty |[@irvin2019] |
| **ChestX-ray14** (NIH) | Chest X-ray | 112,120 images / 30,805 patients | 14 labels mined from reports |[@wang2017] |
| **PadChest** | Chest X-ray | 160,868 images / ~67,000 patients | Spanish; 174 findings, multi-view |[@bustos2020] |
| **LIDC-IDRI** | Chest CT | 1,018 scans | 4-radiologist nodule annotations |[@armato2011] |
| **BraTS / TCGA glioma** | Brain MRI (4 sequences) | hundreds of cases | Expert tumor segmentations; the benchmark for glioma |[@bakas2017; @menze2015] |
| **RSNA ICH** | Head CT | >25,000 exams | Intracranial hemorrhage, 60+ radiologist labelers | |
| **EMBED** | Mammography (2D/DBT) | 3.4M images / ~110,000 patients | Racially balanced; 20% public via AWS |[@jeong2023] |
| **fastMRI** | Knee/brain MRI | >1,500 knee + ~7,000 brain raw studies | Raw *k*-space — for reconstruction research |[@knoll2020] |
| **UK Biobank imaging** | Whole-body MRI/DXA | 100,000 participants | Population cohort, healthy-skewed; access-controlled |[@littlejohns2020] |
| **RadImageNet** | CT, MRI, US | 1.35M images / 131,872 patients | Multi-center |[@meiRadImageNetOpenRadiologic2022] |

Datasets tend to be smaller due to patient privacy, difficulty in recruiting patients with uncommon conditions, and need for expert annotation. These same considerations also mean that some datasets are only available upon request or application. If you like filling out IRB applications, you've chosen the right field.

It is up to the machine learning practicioner to decide 

### It's not all bad
I don't want to be a Debbie Downer. There are some aspects of radiology that make it easier than natural images! 

For instance, radiology images are often acquired in a standardized way, with consistent positioning and orientation. If you're looking at a PA chest radiograph, you can expect the patient to be standing upright, facing the detector, with their arms positioned to rotate the scapulae off the lung fields. The heart is on the left[^situs], and the aortic knob is where it should be. This strong spatial prior can be exploited by models, and registration, atlas-based priors, and even fixed positional encodings work far better here than they would on web images.

[^situs]: Except in *situs inversus* (~1 in 10,000), which is exactly the kind of rare but catastrophic edge case a model trained on the canonical prior will get confidently wrong.

xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


[^situs]: Except in *situs inversus* (~1 in 10,000), which is exactly the kind of
rare but catastrophic edge case a model trained on the canonical prior will get
confidently wrong. Hold that thought; it returns under heterogeneity.

**One channel, calibrated.** Most modalities are grayscale, and — crucially —
the gray values often *mean something physical*. CT is quantitative: each voxel
is a Hounsfield unit, a linear transform of the X-ray attenuation coefficient
$\mu$ relative to water,
$$
\mathrm{HU} = 1000 \times \frac{\mu - \mu_{\text{water}}}{\mu_{\text{water}} - \mu_{\text{air}}},
$$
so water is $0$, air is $-1000$, fat is around $-100$, and cortical bone is
$+1000$ or more. Fat is fat in every CT scanner on Earth. Nothing in RGB is
calibrated like this; "how blue is the sky" is not a physical constant. You can
and should exploit it — windowing, HU-based preprocessing, and physically
motivated augmentations all follow from it.

**The suspected disease localizes attention.** Clinical imaging arrives with a
*reason for exam*. "Rule out pneumothorax" tells you to look at the pleural line;
"rule out stroke" sends you to the brain parenchyma and vessels. The organ of
interest is usually known, which is a luxury object detection never has.

But each of these advantages has a barb:

- The canonical pose breaks for portable/supine films, pediatric patients, body
  habitus, and post-surgical anatomy.
- HU calibration drifts with scanner, kVp, and contrast timing (more on this
  below), and MRI intensities are *not* standardized at all — a T1 value is only
  meaningful relative to the rest of that one acquisition.
- "The organ of interest is known" is a trap: incidental findings in the
  *other* organs are often what matter most clinically. The lung-nodule model
  that ignores the adrenal mass at the edge of the field has failed the patient
  even if its AUC is perfect.

So: use the priors, but treat every one of them as a covariate that can shift.

# The needle in the haystack: subtlety and extreme imbalance

Here is the single biggest statistical difference from natural images. In
COCO, the object you care about typically occupies a meaningful fraction of the
frame. In radiology, the finding is often a handful of voxels in a sea of normal
tissue, and the difference between *malignant* and *benign* — between *call the
patient back* and *see you in two years* — can come down to a few millimeters of
spiculation or a subtle change in density.

Make it concrete with geometry. A chest CT of roughly $512 \times 512 \times 320$
voxels at $0.7 \times 0.7 \times 1.0\,\text{mm}$ contains about $8.4 \times 10^7$
voxels. A clinically important $5\,\text{mm}$ pulmonary nodule is a sphere of
volume $\tfrac{4}{3}\pi r^3 \approx 65\,\text{mm}^3$, or about $134$ voxels. The
lesion is therefore
$$
\frac{134}{8.4\times 10^7} \approx 1.6 \times 10^{-6}
$$
of the volume — roughly **one in six hundred thousand voxels**. Shrink it to a
$3\,\text{mm}$ nodule and you are at one in *three million*. Figure 1 puts
several findings on the same axis as natural-image objects; note the five-to-six
order-of-magnitude gap.

![**Figure 1.** The fraction of an image that actually belongs to the finding,
on a log scale. Natural-image objects (blue) occupy $10^{-3}$ to $10^{0}$ of the
frame. Clinically critical lesions (red/navy) sit at $10^{-7}$ to $10^{-5}$.
This five-to-six order-of-magnitude difference is why naive pixel-wise losses
and patch samplers fail in radiology.](figures/needle_in_haystack.png)

The consequences for an ML scientist are direct:

- **Accuracy is meaningless and pixel-wise loss is treacherous.** A segmentation
  model that predicts "no lesion" everywhere achieves $1 - 1.6\times10^{-6}
  \approx 99.9998\%$ voxel accuracy. Use overlap and detection metrics built for
  imbalance — Dice / $F_1$, where for prediction $P$ and ground truth $G$,
  $$\mathrm{Dice} = \frac{2|P \cap G|}{|P| + |G|},$$
  free-response ROC (FROC) for detection, and class-balanced or region-based
  losses (Dice loss, Tversky, focal). The focal loss down-weights the easy
  negatives that otherwise dominate the gradient:
  $\mathrm{FL}(p_t) = -(1-p_t)^{\gamma}\log p_t$.
- **Most of the volume is uninteresting, and uninteresting in a structured
  way.** Hard-negative mining, lesion-aware patch sampling, and two-stage
  candidate-then-classify pipelines exist because uniformly sampling voxels
  wastes almost all of your compute on obvious lung parenchyma.
- **Resolution is not negotiable.** Downsampling a natural image to $224^2$
  loses a cat's whiskers; downsampling a CT slice can erase the lesion entirely.
  The signal you are hunting may be at the Nyquist limit of the acquisition.

# Annotation is the bottleneck, not the model

In natural-image land, labels are cheap: crowdworkers draw boxes, and "is this a
dog" needs no credential. Radiology inverts this completely, and it reshapes
what is feasible.

**A bounding box is the wrong primitive, and often impossible.** Many findings
have no crisp boundary. Where exactly does a ground-glass opacity end and normal
lung begin? What is the bounding box of diffuse interstitial disease, or of
"the lungs look hyperinflated"? The pathology is frequently a texture or a
*global* property, not a localizable object. Even when a lesion is discrete, it
lives in 3D — a box becomes a volume, and a radiologist scrolling 320 slices to
contour a tumour is spending clinical time that costs orders of magnitude more
than a crowdworker.

**Ground truth is noisy and sometimes unobtainable from the image alone.** The
honest label often is not in the pixels. Is that lung nodule malignant? The
image cannot say; you need the biopsy, or two years of follow-up showing growth.
This is why so many "labels" in public datasets are actually *NLP-extracted from
the radiology report* (MIMIC-CXR, CheXpert, ChestX-ray14, PadChest all do this)
— which means your labels inherit both the radiologist's error rate *and* the
text-mining model's error rate.

**Inter-reader variability is a hard ceiling.** Radiologists disagree. The
LIDC-IDRI lung-nodule database was annotated by four thoracic radiologists
precisely because no single read is ground truth; of 2,669 lesions marked as
nodules $\geq 3\,\text{mm}$ by at least one reader, only about 35% were marked
by all four. If your "ground truth" is one radiologist, your evaluation noise
floor may be larger than the improvement you are claiming. Model the labels as
noisy: capture annotator agreement (e.g. Cohen's / Fleiss' $\kappa$), train
against multi-reader consensus where you can, and report performance relative to
the inter-reader band, not to an imagined perfect oracle.

**You cannot read the data without domain knowledge.** A computer-vision
engineer can sanity-check an ImageNet pipeline by eye. Almost no ML scientist
can look at a FLAIR hyperintensity and tell whether the label is right. This has
a practical implication that teams underestimate: *you need a radiologist in the
loop continuously*, not just at the start, because data-cleaning decisions
(which views to keep, how to handle priors, what counts as positive) are
clinical judgments in disguise.

# The data scarcity problem

Natural-image research rides on ImageNet ($1.4$M images), and webscale sets in
the billions. Radiology has nothing remotely comparable that is *public*, and
the reasons are structural: images are protected health information, they must
be de-identified (including burned-in pixel annotations and faces
reconstructable from head CT/MRI), and the expert labels are expensive. What we
do have is a handful of landmark public collections, summarized in Table 1.

Table: Major public medical-imaging datasets. "Images" counts vary by modality
(a CT/MRI "study" is a 3D volume of many slices). Sizes are as reported by the
source publications.

| Dataset | Modality | Scale | Notes | Ref. |
| --- | --- | --- | --- | --- |
| **TCIA** (The Cancer Imaging Archive) | CT/MR/PET, many | Umbrella of 100+ collections | The host for most public oncology imaging, incl. LIDC-IDRI, BraTS sources |[@clark2013] |
| **MIMIC-CXR** | Chest X-ray | 377,110 images / 227,835 studies / 65,379 patients | Single US center; paired free-text reports |[@johnson2019] |
| **CheXpert** | Chest X-ray | 224,316 images / 65,240 patients | Stanford; 14 NLP-mined labels with uncertainty |[@irvin2019] |
| **ChestX-ray14** (NIH) | Chest X-ray | 112,120 images / 30,805 patients | 14 labels mined from reports |[@wang2017] |
| **PadChest** | Chest X-ray | 160,868 images / ~67,000 patients | Spanish; 174 findings, multi-view |[@bustos2020] |
| **LIDC-IDRI** | Chest CT | 1,018 scans | 4-radiologist nodule annotations |[@armato2011] |
| **BraTS / TCGA glioma** | Brain MRI (4 sequences) | hundreds of cases | Expert tumor segmentations; the benchmark for glioma |[@bakas2017; @menze2015] |
| **RSNA ICH** | Head CT | >25,000 exams | Intracranial hemorrhage, 60+ radiologist labelers | |
| **EMBED** | Mammography (2D/DBT) | 3.4M images / ~110,000 patients | Racially balanced; 20% public via AWS |[@jeong2023] |
| **fastMRI** | Knee/brain MRI | >1,500 knee + ~7,000 brain raw studies | Raw *k*-space — for reconstruction research |[@knoll2020] |
| **UK Biobank imaging** | Whole-body MRI/DXA | 100,000 participants | Population cohort, healthy-skewed; access-controlled |[@littlejohns2020] |

Two things to internalize. First, the largest *labeled* sets are 2D chest
radiographs, because they are the cheapest to acquire and the easiest to label
from reports; 3D, multi-sequence, and rarer-modality data are one to three
orders of magnitude smaller. Second — and this is the setup for the rest of the
post — **a big total $N$ is not the same as a big $N$ where it counts.** EMBED
has 3.4M images, but if you want to evaluate performance for, say,
architectural distortion in dense breasts of women under 40 scanned on one
vendor's tomosynthesis unit, you are suddenly working with a few dozen cases.

# Heterogeneity and generalization: the part everyone underestimates

Everyone says medical-imaging AI "doesn't generalize." Fewer people say *why*,
mechanistically. The reason is that a medical image is the output of a long
physical and human pipeline, and **every stage of that pipeline is a covariate
that differs across hospitals.** A natural image has confounders too (lighting,
camera), but nothing like this stack.

Formally, the trouble is distribution shift. Your model learns
$P_{\text{train}}(Y \mid X)$ over inputs drawn from $P_{\text{train}}(X)$, and is
deployed where both can differ:
$$
P_{\text{train}}(X, Y) \;\neq\; P_{\text{test}}(X, Y).
$$
Decompose it. **Covariate shift** is $P(X)$ changing while $P(Y\mid X)$ holds —
a different scanner renders the *same* pathology with different texture.
**Label shift** is $P(Y)$ changing — disease prevalence differs across a
referral center and a screening clinic, which (via Bayes) moves every predicted
probability and every PPV even if the imaging is identical. **Concept shift** is
the genuinely dangerous one, $P(Y\mid X)$ itself changing — the imaging
appearance of a disease differs by population, or the label definition differs
by institution. Here is the catalogue of what actually shifts:

- **Scanner vendor and model.** GE, Siemens, Philips, Canon detectors and
  reconstruction software impose vendor-specific texture and noise signatures.
  Models readily learn the *scanner*, not the disease.
- **Acquisition physics.** CT: tube voltage (kVp), tube current (mAs), pitch,
  slice thickness, and especially the **reconstruction kernel** (sharp vs.
  smooth) dramatically change texture — reconstruction kernel alone can render
  the majority of radiomic features non-reproducible across settings. MRI: field
  strength (1.5T vs 3T), pulse sequence and vendor implementation, TR/TE, and
  the fact that intensities are not standardized at all.
- **Contrast and timing.** With vs. without IV contrast, and *when* in the
  contrast bolus the scan was captured, can change a structure's appearance
  more than disease does.
- **Imaging noise and dose.** Low-dose protocols (and the shift toward them)
  raise quantum noise; denoising and dose vary by site and by patient size.
- **Patient demographics and disease spectrum.** Age, sex, body habitus,
  ancestry, comorbidity mix, and *disease prevalence and severity* all vary by
  catchment. A model tuned where pneumothoraces are large and obvious degrades
  where they are small and subtle.
- **Protocol and positioning.** Portable vs. fixed units, supine vs. upright,
  inspiration depth, pediatric protocols, post-surgical hardware.

The canonical demonstration is Zech et al.[@zech2018]: CNNs trained to detect
pneumonia on chest radiographs generalized *worse* to outside hospitals than
internal test performance suggested, and the models had learned to detect the
*hospital system and even the department* — exploiting that a portable scanner
marker or a prevalence difference correlated with disease. The same pattern
shows up in segmentation: AlBadawy et al.[@albadawy2018] found glioma-segmentation
performance dropped measurably when training and test institutions differed.
This is shortcut learning, and it is rampant precisely because the spurious
features (scanner, view, burned-in markers) are *so* predictable.

What this means for your workflow:

- **Internal test performance is an upper bound, not an estimate.** The only
  trustworthy evaluation is external — a held-out *site*, ideally a held-out
  *vendor* and *time period*. Split by hospital, not by image.
- **Audit for shortcuts.** Saliency maps that point at the corner marker, an
  AUC that survives when you black out the anatomy, a model that can classify
  scanner from the image — all are red flags.
- **Harmonize deliberately.** Intensity normalization, resampling to common
  spacing, vendor-aware augmentation, and even learned kernel/stain-style
  conversion exist to fight covariate shift; use them, but verify they did not
  erase the signal.

# The statistical-power trap, in numbers

Now combine the previous two sections — heterogeneity *and* scarcity — and you
get the quietest failure mode in the field. To *prove* a model generalizes, you
must evaluate it in each clinically relevant subgroup. But every stratification
you add slices your sample, and because disease is rare, it is the **positive
cases** that vanish first.

Walk it down for a chest-radiograph model, anchored to MIMIC-CXR's 377,110
images (Figure 2). Keep frontal views only ($\times 0.65$). Keep the positives
for your target finding — pneumothorax, prevalence $\approx 3\%$ ($\times 0.03$);
already you are at ~7,000 positive cases, not 377,110. Now ask the
generalization questions clinicians will ask: how does it do in **women**
($\times 0.47$), specifically those **aged 18–40** ($\times 0.16$), specifically
scanned on **vendor B** ($\times 0.30$), specifically with the
**moderate-to-large, actionable** subtype ($\times 0.40$)? You land on about
**66 positive cases**. From 377,110 to 66 — and 66 is the number that actually
governs what you can conclude about that subgroup.

![**Figure 2.** The stratification waterfall. Each clinically reasonable filter
multiplies the count down. The binding constraint is the number of *positive*
(diseased) cases, which collapses fastest because disease is
rare.](figures/stratification_waterfall.png)

Why 66 is a problem is pure sampling theory. Estimate a subgroup sensitivity
(true positive rate) $\hat{p}$ from $n$ positive cases; its standard error is
$\sqrt{p(1-p)/n}$, so the 95% confidence half-width is about
$$
1.96\sqrt{\frac{p(1-p)}{n}}.
$$
At a true sensitivity of $0.85$ and $n = 66$, that half-width is $\pm 0.086$:
your estimate is "somewhere between $0.76$ and $0.94$." You cannot distinguish a
clinically excellent $0.90$ from a borderline $0.78$. (For small $n$ use the
Wilson interval rather than this normal approximation — the qualitative story is
the same, and at these counts it matters.) Figure 3a shows the half-width
shrinking only as $1/\sqrt{n}$; the subgroup strata are marked.

Worse, suppose you want to *detect* a real subgroup gap — say sensitivity drops
from $0.85$ overall to $0.75$ in young women on vendor B. The number of positives
per group needed for a two-sided test at $\alpha = 0.05$ with power $1-\beta$ is
$$
n = \frac{\left(z_{1-\alpha/2}\sqrt{2\bar{p}(1-\bar{p})} +
z_{1-\beta}\sqrt{p_1(1-p_1)+p_2(1-p_2)}\right)^2}{(p_1 - p_2)^2},
$$
which for $p_1=0.85,\, p_2=0.75$ works out to about **250 positive cases per
group** for 80% power. Your subgroup has 66, which buys roughly **30% power**
(Figure 3b): a two-in-three chance of *missing* a real, clinically meaningful
degradation. And if you honestly test across, say, ten subgroups, a Bonferroni
correction to $\alpha = 0.005$ pushes the requirement to ~425 per group — while
simultaneously, *not* correcting means some of your "significant" subgroup
findings are noise. You are squeezed from both sides.

![**Figure 3.** What those counts buy. **(a)** The 95% CI half-width on a
subgroup sensitivity estimate shrinks only as $1/\sqrt{n}$; at $n=66$ positives
you have $\pm 0.09$ precision. **(b)** Power to detect a $0.85 \to 0.75$
sensitivity drop: you need ~250 positives per group for 80% power, but the
deepest subgroup has 66, giving ~30% power.](figures/power_and_precision.png)

The lesson is not "give up." It is to **plan evaluation as a power calculation
from day one**: decide which subgroups are non-negotiable, estimate the positive
counts you will actually have, and either acquire enough cases (often via
multi-site collaboration) or state honestly which subgroups you are *not*
powered to certify. Silent truncation — reporting one headline AUC computed over
a population you never stratified — is how models that look published-ready fail
in deployment.

# How these models are actually regulated

If your model will touch patient care in the US, it is almost certainly a
*medical device*, and the FDA's framework shapes your engineering. A few facts
ML scientists are routinely surprised by:

- **Radiology dominates.** From the 1990s through the mid-2020s, roughly
  **three-quarters of all FDA-authorized AI/ML-enabled devices are in
  radiology** — by far the largest category. This is your field.
- **Almost everything clears via 510(k), not clinical trials.** The dominant
  path is the **510(k)**, which establishes "substantial equivalence" to a
  legally marketed *predicate* device — *not* a randomized trial. (Genuinely
  novel devices use the **De Novo** path; the highest-risk ones need full
  premarket approval, **PMA**, which is rare for imaging AI.) A consequence:
  fewer than a third of FDA-authorized radiology AI devices have published
  prospective clinical testing. Substantial equivalence is a regulatory claim,
  not evidence your model helps patients — keep those separate in your head.
- **Models had to be "locked."** Historically the FDA cleared **locked**
  algorithms — same input, same output, no learning in the field — because a
  continuously adapting model breaks the entire premarket paradigm.

What changed recently is worth knowing, because it directly affects how you can
plan model updates. In December 2024 the FDA finalized guidance on the
**Predetermined Change Control Plan (PCCP)**. The idea: in your original
submission, you pre-specify *what* you will be allowed to change (e.g. retrain on
new sites, recalibrate a threshold), the *methodology* you will use to develop
and validate each change, and an *impact assessment* — and then you can ship
those pre-authorized modifications without a new marketing submission. For an ML
scientist this is the bridge from "frozen forever" toward "responsibly
updatable," and it explicitly asks you to think up front about intended-use
populations (ethnicity, sex, disease severity) and deployment environments. In
practice it means your *monitoring and revalidation plan is part of the product*,
not an afterthought.

# The academic model is not the deployed model

Finally, the gap that ends the most promising projects. The model in the paper
and the model in the hospital are different artifacts, optimized against
different objectives.

| Dimension | Academic / benchmark model | Deployed clinical model |
| --- | --- | --- |
| **Objective** | Maximize AUC/Dice on a fixed test set | Improve a clinical workflow at a fixed, safe operating point |
| **Metric that matters** | Discrimination (AUROC) | Sensitivity/specificity at a *chosen* threshold; calibration; PPV at local prevalence |
| **Data** | Curated, deduplicated, clean labels | Messy PACS feed: priors, wrong views, artifacts, truncation |
| **Generalization** | Random split, often single site | Must hold across vendors, sites, time, demographics |
| **Failure cost** | A lower number in a table | A missed cancer or a false alarm that fatigues the radiologist |
| **Lifecycle** | Frozen at publication | Monitored, drifts, must be revalidated and re-cleared |
| **Integration** | A `.ipynb` and a checkpoint | DICOM in/out, PACS + reporting integration, latency budget, audit trail |

Concretely, what bites teams crossing this gap:

- **Operating point, not the whole curve.** A clinician runs your model at *one*
  threshold. A great ROC curve with no defensible, *calibrated* operating point
  is not deployable. And because prevalence differs by site (label shift), the
  threshold that gives the right PPV in your lab is wrong in the clinic; plan to
  recalibrate, e.g. with Platt scaling or isotonic regression, per site.
- **The long tail is the job.** Benchmarks delete the ambiguous and corrupted
  cases that dominate a real PACS queue. In deployment those *are* the workload:
  the lateral mistakenly sent as frontal, the patient with prior surgery, the
  motion-degraded study. Your model needs a calibrated "I don't know."
- **Prospective $\neq$ retrospective.** Retrospective AUC routinely overstates
  prospective performance; the few prospective and randomized radiology-AI
  studies have repeatedly come in below their retrospective hype.
- **Automation bias and workflow effects.** A deployed model changes radiologist
  behavior — sometimes it catches misses, sometimes it anchors the reader to a
  wrong call. The endpoint that matters is *reader + model*, not the model in
  isolation.
- **Drift and monitoring.** Scanners get replaced, protocols change, populations
  shift. A model that was validated in 2024 is not automatically valid in 2027.
  The PCCP framework above exists precisely because this drift is inevitable.

# Takeaways

If you remember five things moving from natural images to radiology:

1. **Exploit the priors, distrust them.** Canonical pose, calibrated intensities,
   and a known organ of interest are real gifts — but each is a covariate that
   shifts, and the finding may be in the organ you weren't told to look at.
2. **Your signal is a needle.** Lesions are $10^{-7}$–$10^{-5}$ of the image.
   Abandon accuracy and pixel-wise loss; use detection/overlap metrics,
   imbalance-aware losses, and lesion-aware sampling, and don't downsample away
   the disease.
3. **Labels are the bottleneck.** They are expensive, noisy, NLP-mined, and
   bounded by inter-reader disagreement. Keep a radiologist in the loop and
   model the label noise explicitly.
4. **Generalization is the whole game.** Split by site/vendor/time, hunt for
   shortcuts, and treat internal test numbers as upper bounds.
5. **Power your evaluation before you train.** Stratification destroys positive
   counts; decide which subgroups you can certify, and say so honestly. Then
   remember the deployed model lives at one calibrated operating point, under FDA
   rules, drifting over time — design for that from the start.

See the accompanying `notebook.ipynb` for the geometry, the stratification
waterfall, the power calculations behind Figures 1–3, and an automated check
that every citation below resolves.
