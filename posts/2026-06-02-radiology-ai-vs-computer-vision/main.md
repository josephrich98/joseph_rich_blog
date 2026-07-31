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
Radiology is the medical specialty that uses imaging to diagnose and treat disease. Radiological imaging allows for visualization of entire tissues or organs in the body, which differentiates radiology from cellular-based imaging that is common in genomics and pathology. The most common reasons for radiology imaging are trauma and injuries (broken bones, internal bleeding), cancer (tumor detection, staging, and monitoring), and chronic diseases (heart disease, liver disease, lung disease). 

Images are organized hierarchically. Each 2D image is called a slice, and a series of slices can be stacked to form a 3D volume, or a series. A study is comprised of one or more series, and a patient can have multiple studies. For instance, a patient may have a chest CT study with two series: one without contrast and one with contrast. One patient can have multiple studies over time, such as a chest CT study in 2020 and a follow-up chest CT study in 2022.

The most common modalities are X-ray, CT, MRI, ultrasound, and nuclear medicine (PET/SPECT). X-ray and CT use ionizing radiation to produce images. The more signal a tissue blocks, the whiter it appears on the image. X-rays are commonly used for bone and chest imaging. A CT scan is a series of X-ray images taken from different angles and reconstructed into a 3D volume. A 3D pixel is called a voxel. There are three possible slice orientations: axial (top-down), coronal (front-back), and sagittal (side). CT is commonly used for chest, abdominal, and brain imaging. MRI uses magnetic fields and radio waves (the same technology as proton nuclear magnetic resonance), also capturing 3D volumes. MRI enables soft tissue visualization in higher detail compared to CT, and has the advantage of not using ionizing radiation. Ultrasound uses high-frequency sound waves, and is commonly used for obstetrics, cardiology, and abdominal imaging. Nuclear medicine uses radioactive tracers to visualize physiological processes, used in diagnostic procedures such as studying brain activity and thyroid function.

![**Figure 1**](figures/imaging_modalities.png)

**Figure 1**: Imaging modalities. Made with ChatGPT.

## Radiology and computer vision similarities and differences
Let me blow your mind: radiology images are a type of image. They're a grid of pixels, just like any other image, even if it is less visually stimulating to look at a picture of lung opacities than a picture of a dog. This means that all the same computer vision architectures that work on natural images can be applied to radiology images.

<div style="display: flex; flex-wrap: wrap; gap: 1.5rem; justify-content: center; align-items: flex-start; margin: 1.5rem 0;">
  <figure style="margin: 0; text-align: center;">
    <img src="figures/lung.jpg" alt="Chest radiograph showing lung opacities" style="height: 240px; width: auto; border-radius: 4px;">
    <figcaption style="font-size: 0.9em; margin-top: 0.5rem; text-align: center;">
      A picture of lung opacities.<br>
      Source: <a href="https://radiologyassistant.nl/chest/chest-x-ray/lung-disease">Radiology Assistant</a>.
    </figcaption>
  </figure>
  <figure style="margin: 0; text-align: center;">
    <img src="figures/dog_in_suit.jpeg" alt="A dog wearing a business suit" style="height: 240px; width: auto; border-radius: 4px;">
    <figcaption style="font-size: 0.9em; margin-top: 0.5rem; text-align: center;">
      A picture of a dog in a suit.<br>
      Source: <a href="https://www.amazon.com/Rubies-unisex-Business-Costume-Multicolor/dp/B01C4K8334">Rubies</a>.
    </figcaption>
  </figure>
</div>

However, there are some important differences between radiology and natural images that make radiology a unique domain for machine learning.

### Annotation requires domain expertise

It takes substantial medical training even to recognize the anatomy in a radiology image, let alone to identify pathology. Patients can have substantial variability in their anatomy, which can make it difficult to discern disease from normal variation. Tumors can come in all shapes and sizes, sometimes making them difficult to identify from surrounding tissue, cysts, or other benign findings. Some diseases have highly characteristic imaging appearances—for example, the boot-shaped heart of tetralogy of Fallot or the coffee bean sign of sigmoid volvulus. However, many diseases exhibit substantial variability across patients. For instance, pneumonia may appear as focal lobar consolidation, patchy multifocal opacities, diffuse interstitial infiltrates, or even be nearly occult on early imaging. This diversity makes medical image interpretation a challenging pattern-recognition task.

### Most pixels are uninformative; a few pixels can make the difference
In many computer vision tasks, the object of interest occupies a significant portion of the image. Think of a digit in an MNIST image, or a cat in a COCO image. In these cases, the object is large enough that it can be easily detected and classified by a model. In radiology, however, the finding is often a small fraction of the image, and the difference between a benign and malignant finding can be subtle. For example, a small pulmonary nodule may only occupy a few pixels in a CT scan, but its presence or absence can have significant clinical implications.

![**Figure 2**](figures/needle_in_haystack.png)

**Figure 2**: The fraction of an image that actually belongs to the finding,
on a log scale. Natural-image objects (blue) occupy $10^{-3}$ to $10^{0}$ of the
frame. Clinically critical lesions (red/navy) sit at $10^{-7}$ to $10^{-5}$.
This five-to-six order-of-magnitude difference is why naive pixel-wise losses
and patch samplers fail in radiology.

As a concrete example, let's consider a chest CT scan. A chest CT of roughly $512 \times 512 \times 320$ voxels at $0.7 \times 0.7 \times 1.0\,\mathrm{mm}$ contains about $8.4 \times 10^7$
voxels. A clinically important $5\,\mathrm{mm}$ pulmonary nodule is a sphere of
volume $\tfrac{4}{3}\pi r^3 \approx 65\,\mathrm{mm}^3$, or about $134$ voxels. The
lesion is therefore
$$
\frac{134}{8.4\times 10^7} \approx 1.6 \times 10^{-6}
$$
of the volume — roughly one in six hundred thousand voxels. Figure 2 puts
several findings on the same axis as natural-image objects; note the five-to-six
order-of-magnitude gap.

This gap means that pixelwise accuracy is a poor metric for evaluating
segmentation model performance. A model that predicts "no lesion" everywhere
achieves a voxel accuracy of $1 - 1.6\times10^{-6}$, or $99.99984\%$. Use
overlap and detection metrics built for imbalance instead. Dice (equivalently
$F_1$), for a prediction $P$ and ground truth $G$, is

$$
\mathrm{Dice} = \frac{2|P \cap G|}{|P| + |G|},
$$

and free-response ROC (FROC) is the standard for detection. Pair these with
class-balanced or region-based losses (Dice loss, Tversky, focal). The focal
loss down-weights the easy negatives that otherwise dominate the gradient:

$$
\mathrm{FL}(p_t) = -(1-p_t)^{\gamma}\log p_t.
$$

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

There is often a tradeoff that must be made between data size and homogeneity. For instance, if you're working on kidney cancer, you have access to ~500 cases from the KiTS23 dataset, and ~200 cases from the TCGA-KIRC dataset. Pooling these datasets means mixing institutions, protocols, and scanners, which can introduce heterogeneity that may hurt model performance. One can add in the MRI cases from TCGA-KIRC, but that adds a new modality and a new set of heterogeneity. One can add additional abdominal CT datasets, but that adds even more institutions and disease types. The right choice depends on the task, the model, and the evaluation strategy.

Stratifying by covariates can help for studying specific subgroups, but it comes with a tradeoff in statistical power. For example, let's consider a chest x-ray model for pneumothorax (Figure 3). Keep frontal views only ($\times 0.65$). Keep the positives
for your target finding — pneumothorax, prevalence $\approx 3\%$ ($\times 0.03$);
already you are at ~7,000 positive cases, not 377,110. Now ask the
generalization questions clinicians will ask: how does it do in **women**
($\times 0.47$), specifically those **aged 18–40** ($\times 0.16$), specifically
scanned on **vendor B** ($\times 0.30$), specifically with the
**moderate-to-large, actionable** subtype ($\times 0.40$)? You land on about
**66 positive cases**. From 377,110 to 66 — and 66 is the number that actually
governs what you can conclude about that subgroup.

![**Figure 3**](figures/stratification_waterfall.png)

**Figure 3**: The stratification waterfall. Each clinically reasonable filter
multiplies the count down. The binding constraint is the number of positive
(diseased) cases, which collapses fastest because disease is
rare.

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
the same, and at these counts it matters.) Figure 4a shows the half-width
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
(Figure 4b): a two-in-three chance of *missing* a real, clinically meaningful
degradation. And if you honestly test across, say, ten subgroups, a Bonferroni
correction to $\alpha = 0.005$ pushes the requirement to ~425 per group — while
simultaneously, *not* correcting means some of your "significant" subgroup
findings are noise. You are squeezed from both sides.

![**Figure 4**](figures/power_and_precision.png)

**Figure 4**: What those counts buy. **(a)** The 95% CI half-width on a
subgroup sensitivity estimate shrinks only as $1/\sqrt{n}$; at $n=66$ positives
you have $\pm 0.09$ precision. **(b)** Power to detect a $0.85 \to 0.75$
sensitivity drop: you need ~250 positives per group for 80% power, but the
deepest subgroup has 66, giving ~30% power.

The lesson is not "give up." It is to **plan evaluation as a power calculation
from day one**: decide which subgroups are non-negotiable, estimate the positive
counts you will actually have, and either acquire enough cases (often via
multi-site collaboration) or state honestly which subgroups you are *not*
powered to certify. Silent truncation — reporting one headline AUC computed over
a population you never stratified — is how models that look published-ready fail
in deployment.

### It's not all bad
I don't want to be a Debbie Downer. There are some aspects of radiology that make it easier than natural images! 

For instance, radiology images are often acquired in a standardized way, with consistent positioning and orientation. If you're looking at a PA chest radiograph, you can expect the patient to be standing upright, facing the detector, with their arms positioned to rotate the scapulae off the lung fields. The heart is on the left[^situs], and the aortic knob is where it should be. This strong spatial prior can be exploited by models, and registration, atlas-based priors, and even fixed positional encodings work far better here than they would on web images.

[^situs]: Except in *situs inversus* (~1 in 10,000), which is exactly the kind of rare but catastrophic edge case a model trained on the canonical prior will get confidently wrong.

Most modalities are grayscale, which removes any complexity added by color channels. For x-ray and CT, the pixel/voxel value has a physical meaning, which can be directly exploited. CT values are measured in Hounsfield units, which are a linear transformation of the X-ray attenuation coefficient relative to water. This means that a voxel value of 0 corresponds to water, -1000 corresponds to air, and +1000 corresponds to cortical bone. This calibration allows for physically motivated preprocessing and augmentations. For instance, preprocessing to calculate fat fraction or bone density can be done directly from the voxel values, and augmentations can be designed to simulate changes in tissue density or contrast.

Finally, radiology images often come with a reason for the exam, which can help localize attention. For example, if the reason for the exam is "rule out pneumothorax," the model can focus on the pleural line. However, this prior should be treated as a covariate that can shift, as incidental findings in other organs may be clinically important. Additionally, sometimes useful information might be outside the organ of focus. For instance, when training a kidney-cancer model, it may be tempting to only retain the kidney and surrounding tissue, but the presence of metastases outside the kidney may be the most clinically important finding.


## How these models are regulated

If your model will touch patient care in the US, it is almost certainly a *medical device*, and the FDA's framework shapes your engineering. A few facts ML scientists are routinely surprised by:

- **Radiology dominates.** From the 1990s through the mid-2020s, roughly
  **three-quarters of all FDA-authorized AI/ML-enabled devices are in
  radiology** — by far the largest category.
- **Almost everything clears via 510(k), not clinical trials.** The dominant
  path is the **510(k)**, which establishes "substantial equivalence" to a
  legally marketed *predicate* device — *not* a randomized trial. (Genuinely
  novel devices use the **De Novo** path; the highest-risk ones need full
  premarket approval, **PMA**, which is rare for imaging AI.) A consequence:
  fewer than a third of FDA-authorized radiology AI devices have published
  prospective clinical testing. Substantial equivalence is a regulatory claim,
  not evidence your model helps patients.
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
populations (ethnicity, sex, disease severity) and deployment environments. 
This means that models can be updated in the field, but only in ways that were pre-specified and validated according to the PCCP.

## The leap from academia to the clinic

Many papers are released every day that sound like they've solved a key issue in radiology with AI such as cancer diagnosis, tumor segmentation, or report generation. Some are even published in top-tier journals. But clinical radiology has barely changed. Why? There are a few key features that separate the academic and clinical worlds.

For a paper, the goal is to show that a model can achieve a high AUC or Dice score on a benchmark dataset. For a hospital, the goal is to improve patient outcomes and workflow efficiency. Generalizability is a must. Academic datasets are often curated and cleaned, while hospital data is messy and heterogeneous. The cost of failure is also different: a lower number in a table is not the same as a missed cancer or a false alarm that fatigues the radiologist. The lifecycle of a model is different: academic models are frozen at publication, while clinical models must be monitored for drift and revalidated. And the finished product of an academic paper is a GitHub repository with scripts for running the model and a checkpoint, but this is only the beginning for a hospital. A clinical model must be integrated into the hospital's PACS and reporting systems, comply with HIPAA regulations, and meet latency and audit requirements.

## Conclusion

Radiology AI is an exciting field. The problems are complex, the stakes are high, and the potential for impact is enormous. However, it is not simply a branch of computer vision, and impacting the clinic requires more than just a high AUC on a benchmark dataset. It requires understanding the medical context, the regulatory landscape, and the practical realities of clinical deployment. By keeping these considerations in mind, ML scientists can better navigate the challenges of radiology AI and contribute to meaningful improvements in patient care.