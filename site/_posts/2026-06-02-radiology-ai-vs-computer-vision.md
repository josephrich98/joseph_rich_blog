---
title: "Radiology AI Is Not Computer Vision: A Field Guide for ML Scientists"
date: 2026-06-02
permalink: /posts/2026/06/radiology-ai-vs-computer-vision/
repro_url: https://github.com/josephrich98/joseph_rich_blog/tree/main/posts/2026-06-02-radiology-ai-vs-computer-vision
excerpt: "A field guide for ML scientists working in radiology imaging. How is radiology similar to standard computer vision, and how is it different? This post covers a radiology primer, some medical context that makes radiology data different from standard imaging, some widely-used radiology datasets, and some popular radiology AI models."
tags:
  - machine learning
  - radiology
  - computer vision
  - medical imaging
toc: true
comments: true
---
<!-- Generated from posts/2026-06-02-radiology-ai-vs-computer-vision/main.md by scripts/sync_posts.py. Do not edit here; edit the source and re-commit. -->


## Radiology primer
Radiology is the medical specialty that uses imaging to diagnose and treat disease. Radiological imaging allows for visualization of entire tissues or organs in the body, which differentiates radiology from cellular-based imaging that is common in genomics and pathology. The most common causes for radiology imaging trauma and injuries (broken bones, internal bleeding), cancer (tumor detection, staging, and monitoring), and chronic diseases (heart disease, liver disease, lung disease). 

Images are organized heirarchically. Each 2D image is called a slice, and a series of slices can be stacked to form a 3D volume, or a series. A study is comprised of one or more series, and a patient can have multiple studies. For instance, a patient may have a chest CT study with two series: one without contrast and one with contrast. One patient can have multiple studies over time, such as a chest CT study in 2020 and a follow-up chest CT study in 2022.

The most common modalities are X-ray, CT, MRI, ultrasound, and nuclear medicine (PET/SPECT). X-ray and CT use ionizing radiation to produce images. The more signal a tissue blocks, the whiter it appears on the image. X-rays are commonly used for bone and chest imaging. A CT scan is a series of X-ray images taken from different angles and reconstructed into a 3D volume. A 3D pixel is called a voxel. There are three possible slice orientations: axial (top-down), coronal (front-back), and sagittal (side). CT is commonly used for chest, abdominal, and brain imaging. MRI uses magnetic fields and radio waves (the same technology as proton nuclear magnetic resonance), also capturing 3D volumes. MRI enables soft tissue visualization in higher detail compared to CT, and has the advantage of not using ionizing radiation. Ultrasound uses high-frequency sound waves, and is commonly used for obstetrics, cardiology, and abdominal imaging. Nuclear medicine uses radioactive tracers to visualize physiological processes, used in diagnostic procedures such as studying brain activity and thyroid function.

![**Figure 1**](/images/posts/2026-06-02-radiology-ai-vs-computer-vision/imaging_modalities.png)

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

![**Figure 1**](/images/posts/2026-06-02-radiology-ai-vs-computer-vision/needle_in_haystack.png)

**Figure 1**: The fraction of an image that actually belongs to the finding,
on a log scale. Natural-image objects (blue) occupy $$10^{-3}$$ to $$10^{0}$$ of the
frame. Clinically critical lesions (red/navy) sit at $$10^{-7}$$ to $$10^{-5}$$.
This five-to-six order-of-magnitude difference is why naive pixel-wise losses
and patch samplers fail in radiology.

As a concrete example, let's consider a chest CT scan. A chest CT of roughly $$512 \times 512 \times 320$$ voxels at $$0.7 \times 0.7 \times 1.0\,\text{mm}$$ contains about $$8.4 \times 10^7$$
voxels. A clinically important $$5\,\text{mm}$$ pulmonary nodule is a sphere of
volume $$\tfrac{4}{3}\pi r^3 \approx 65\,\text{mm}^3$$, or about $$134$$ voxels. The
lesion is therefore

$$
\frac{134}{8.4\times 10^7} \approx 1.6 \times 10^{-6}
$$

of the volume — roughly one in six hundred thousand voxels. Figure 1 puts
several findings on the same axis as natural-image objects; note the five-to-six
order-of-magnitude gap.

This gap means that pixelwise accuracy is a poor metric for evaluating segmentation model performance. A segmentation model that predicts "no lesion" everywhere achieves $$1 - 1.6\times10^{-6} \approx 99.9998\%$$ voxel accuracy. Use overlap and detection metrics built for imbalance — Dice / $$F_1$$, where for prediction $$P$$ and ground truth $$G$$, $$\mathrm{Dice} = \frac{2|P \cap G|}{|P| + |G|},$$ free-response ROC (FROC) for detection, and class-balanced or region-based losses (Dice loss, Tversky, focal). The focal loss down-weights the easy negatives that otherwise dominate the gradient: $$\mathrm{FL}(p_t) = -(1-p_t)^{\gamma}\log p_t$$.

This gap also means that image preprocessing may be necessary before passing through a model. Masking out uninformative regions of the image, such as the background or areas of normal tissue, can help the model focus on the relevant regions. Additionally, using multi-scale approaches or attention mechanisms can help the model capture small lesions that may be missed at a single scale.

### Data are often scarce and heterogeneous
Natural-image research has access to a wealth of images. ImageNet has 1.4 million images, InfiMNIST can generate effectively infinite images, and webscale datasets have billions of images. Radiology has a few public datasets with over 10,000 images, generally for chest x-ray and/or healthy patients, but most datasets are much smaller. As soon as one focuses on a particular disease, modality, or patient population, they will be hard-pressed to find more than a few hundred images. A few of the most popular public datasets are summarized in Table 1.

| Dataset | Modality | Scale | Notes | Ref. |
| --- | --- | --- | --- | --- |
| **TCIA** (The Cancer Imaging Archive) | CT/MR/PET, many | Umbrella of 100+ collections | The host for most public oncology imaging, incl. LIDC-IDRI, BraTS sources |<sup><a href="#ref-clark2013" role="doc-biblioref">1</a></sup> |
| **MIMIC-CXR** | Chest X-ray | 377,110 images / 227,835 studies / 65,379 patients | Single US center; paired free-text reports |<sup><a href="#ref-johnson2019" role="doc-biblioref">2</a></sup> |
| **CheXpert** | Chest X-ray | 224,316 images / 65,240 patients | Stanford; 14 NLP-mined labels with uncertainty |<sup><a href="#ref-irvin2019" role="doc-biblioref">3</a></sup> |
| **ChestX-ray14** (NIH) | Chest X-ray | 112,120 images / 30,805 patients | 14 labels mined from reports |<sup><a href="#ref-wang2017" role="doc-biblioref">4</a></sup> |
| **PadChest** | Chest X-ray | 160,868 images / ~67,000 patients | Spanish; 174 findings, multi-view |<sup><a href="#ref-bustos2020" role="doc-biblioref">5</a></sup> |
| **LIDC-IDRI** | Chest CT | 1,018 scans | 4-radiologist nodule annotations |<sup><a href="#ref-armato2011" role="doc-biblioref">6</a></sup> |
| **BraTS / TCGA glioma** | Brain MRI (4 sequences) | hundreds of cases | Expert tumor segmentations; the benchmark for glioma |<sup><a href="#ref-bakas2017" role="doc-biblioref">7</a>,<a href="#ref-menze2015" role="doc-biblioref">8</a></sup> |
| **RSNA ICH** | Head CT | >25,000 exams | Intracranial hemorrhage, 60+ radiologist labelers | |
| **EMBED** | Mammography (2D/DBT) | 3.4M images / ~110,000 patients | Racially balanced; 20% public via AWS |<sup><a href="#ref-jeong2023" role="doc-biblioref">9</a></sup> |
| **fastMRI** | Knee/brain MRI | >1,500 knee + ~7,000 brain raw studies | Raw *k*-space — for reconstruction research |<sup><a href="#ref-knoll2020" role="doc-biblioref">10</a></sup> |
| **UK Biobank imaging** | Whole-body MRI/DXA | 100,000 participants | Population cohort, healthy-skewed; access-controlled |<sup><a href="#ref-littlejohns2020" role="doc-biblioref">11</a></sup> |
| **RadImageNet** | CT, MRI, US | 1.35M images / 131,872 patients | Multi-center |<sup><a href="#ref-meiRadImageNetOpenRadiologic2022" role="doc-biblioref">12</a></sup> |

Datasets tend to be smaller due to patient privacy, difficulty in recruiting patients with uncommon conditions, and need for expert annotation. These same considerations also mean that some datasets are only available upon request or application. If you like filling out IRB applications, you've chosen the right field.

There is often a tradeoff that must be made between data size and homogeneity. For instance, if you're working on kidney cancer, you have access to ~500 cases from the KiTS23 dataset, and ~200 cases from the TCGA-KIRC dataset. Pooling these datasets means mixing institutions, protocols, and scanners, which can introduce heterogeneity that may hurt model performance. One can add in the MRI cases from TCGA-KIRC, but that adds a new modality and a new set of heterogeneity. One can add additional abdominal CT datasets, but that adds even more instutitons and disease types. The right choice depends on the task, the model, and the evaluation strategy.

Stratifying by covariates can help for studying specific subgroups, but it comes with a tradeoff in statistical power. For example, let's consider a chest x-ray model for pneumothorax (Figure 2). Keep frontal views only ($$\times 0.65$$). Keep the positives
for your target finding — pneumothorax, prevalence $$\approx 3\%$$ ($$\times 0.03$$);
already you are at ~7,000 positive cases, not 377,110. Now ask the
generalization questions clinicians will ask: how does it do in **women**
($$\times 0.47$$), specifically those **aged 18–40** ($$\times 0.16$$), specifically
scanned on **vendor B** ($$\times 0.30$$), specifically with the
**moderate-to-large, actionable** subtype ($$\times 0.40$$)? You land on about
**66 positive cases**. From 377,110 to 66 — and 66 is the number that actually
governs what you can conclude about that subgroup.

![**Figure 2**](/images/posts/2026-06-02-radiology-ai-vs-computer-vision/stratification_waterfall.png)

**Figure 2.**: The stratification waterfall. Each clinically reasonable filter
multiplies the count down. The binding constraint is the number of positive
(diseased) cases, which collapses fastest because disease is
rare.

Why 66 is a problem is pure sampling theory. Estimate a subgroup sensitivity
(true positive rate) $$\hat{p}$$ from $$n$$ positive cases; its standard error is
$$\sqrt{p(1-p)/n}$$, so the 95% confidence half-width is about

$$
1.96\sqrt{\frac{p(1-p)}{n}}.
$$

At a true sensitivity of $$0.85$$ and $$n = 66$$, that half-width is $$\pm 0.086$$:
your estimate is "somewhere between $$0.76$$ and $$0.94$$." You cannot distinguish a
clinically excellent $$0.90$$ from a borderline $$0.78$$. (For small $$n$$ use the
Wilson interval rather than this normal approximation — the qualitative story is
the same, and at these counts it matters.) Figure 3a shows the half-width
shrinking only as $$1/\sqrt{n}$$; the subgroup strata are marked.

Worse, suppose you want to *detect* a real subgroup gap — say sensitivity drops
from $$0.85$$ overall to $$0.75$$ in young women on vendor B. The number of positives
per group needed for a two-sided test at $$\alpha = 0.05$$ with power $$1-\beta$$ is

$$
n = \frac{\left(z_{1-\alpha/2}\sqrt{2\bar{p}(1-\bar{p})} +
z_{1-\beta}\sqrt{p_1(1-p_1)+p_2(1-p_2)}\right)^2}{(p_1 - p_2)^2},
$$

which for $$p_1=0.85,\, p_2=0.75$$ works out to about **250 positive cases per
group** for 80% power. Your subgroup has 66, which buys roughly **30% power**
(Figure 3b): a two-in-three chance of *missing* a real, clinically meaningful
degradation. And if you honestly test across, say, ten subgroups, a Bonferroni
correction to $$\alpha = 0.005$$ pushes the requirement to ~425 per group — while
simultaneously, *not* correcting means some of your "significant" subgroup
findings are noise. You are squeezed from both sides.

![**Figure 3**](/images/posts/2026-06-02-radiology-ai-vs-computer-vision/power_and_precision.png)

**Figure 3.**: What those counts buy. **(a)** The 95% CI half-width on a
subgroup sensitivity estimate shrinks only as $$1/\sqrt{n}$$; at $$n=66$$ positives
you have $$\pm 0.09$$ precision. **(b)** Power to detect a $$0.85 \to 0.75$$
sensitivity drop: you need ~250 positives per group for 80% power, but the
deepest subgroup has 66, giving ~30% power.](figures/power_and_precision.png)

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

Many papers are released everyday that sound like they've solved a key issue in radiology with AI such as cancer diagnosis, tumor segmentation, or report generation. Some are even published in top-tier journals. But clinical radiology has barely changed. Why? There are a few key features that separate the academic and clinical worlds.

For a paper, the goal is to show that a model can achieve a high AUC or Dice score on a benchmark dataset. For a hospital, the goal is to improve patient outcomes and workflow efficiency. Generalizability is a must. Academic datasets are often curated and cleaned, while hospital data is messy and heterogeneous. The cost of failure is also different: a lower number in a table is not the same as a missed cancer or a false alarm that fatigues the radiologist. The lifecycle of a model is different: academic models are frozen at publication, while clinical models must be monitored for drift and revalidated. And the finished product of an academic paper is a GitHub repository with scripts for running the model and a checkpoint, but this is only the beginning for a hospital. A clinical model must be integrated into the hospital's PACS and reporting systems, comply with HIPAA regulations, and meet latency and audit requirements.

## Conclusion

Radiology AI is an exciting field. The problems are complex, the stakes are high, and the potential for impact is enormous. However, it is not simply a branch of computer vision, and impacting the clinic requires more than just a high AUC on a benchmark dataset. It requires understanding the medical context, the regulatory landscape, and the practical realities of clinical deployment. By keeping these considerations in mind, ML scientists can better navigate the challenges of radiology AI and contribute to meaningful improvements in patient care.

## References

<div id="refs" class="references csl-bib-body" role="list">
<div id="ref-clark2013" class="csl-entry" role="listitem">
<div class="csl-left-margin">1. </div><div class="csl-right-inline"><span class="nocase">Clark K, Vendt B, Smith K, et al.</span> The <span>Cancer</span> <span>Imaging</span> <span>Archive</span> (<span>TCIA</span>): Maintaining and operating a public information repository. <em>Journal of Digital Imaging</em>. 2013;26(6):1045-1057. doi:<a href="https://doi.org/10.1007/s10278-013-9622-7">10.1007/s10278-013-9622-7</a></div>
</div>
<div id="ref-johnson2019" class="csl-entry" role="listitem">
<div class="csl-left-margin">2. </div><div class="csl-right-inline"><span class="nocase">Johnson AEW, Pollard TJ, Berkowitz SJ, et al.</span> <span>MIMIC-CXR</span>, a de-identified publicly available database of chest radiographs with free-text reports. <em>Scientific Data</em>. 2019;6:317. doi:<a href="https://doi.org/10.1038/s41597-019-0322-0">10.1038/s41597-019-0322-0</a></div>
</div>
<div id="ref-irvin2019" class="csl-entry" role="listitem">
<div class="csl-left-margin">3. </div><div class="csl-right-inline"><span class="nocase">Irvin J, Rajpurkar P, Ko M, et al.</span> <span>CheXpert</span>: A large chest radiograph dataset with uncertainty labels and expert comparison. <em>Proceedings of the AAAI Conference on Artificial Intelligence</em>. 2019;33(1):590-597. doi:<a href="https://doi.org/10.1609/aaai.v33i01.3301590">10.1609/aaai.v33i01.3301590</a></div>
</div>
<div id="ref-wang2017" class="csl-entry" role="listitem">
<div class="csl-left-margin">4. </div><div class="csl-right-inline"><span class="nocase">Wang X, Peng Y, Lu L, et al.</span> <span class="nocase">ChestX-ray8</span>: Hospital-scale chest <span class="nocase">X-ray</span> database and benchmarks on weakly-supervised classification and localization of common thorax diseases. <em>IEEE Conference on Computer Vision and Pattern Recognition (CVPR)</em>. Published online 2017:3462-3471. doi:<a href="https://doi.org/10.1109/CVPR.2017.369">10.1109/CVPR.2017.369</a></div>
</div>
<div id="ref-bustos2020" class="csl-entry" role="listitem">
<div class="csl-left-margin">5. </div><div class="csl-right-inline">Bustos A, Pertusa A, Salinas J-M, Iglesia-Vayá M de la. <span>PadChest</span>: A large chest x-ray image dataset with multi-label annotated reports. <em>Medical Image Analysis</em>. 2020;66:101797. doi:<a href="https://doi.org/10.1016/j.media.2020.101797">10.1016/j.media.2020.101797</a></div>
</div>
<div id="ref-armato2011" class="csl-entry" role="listitem">
<div class="csl-left-margin">6. </div><div class="csl-right-inline"><span class="nocase">Armato III SG, McLennan G, Bidaut L, et al.</span> The <span>Lung</span> <span>Image</span> <span>Database</span> <span>Consortium</span> (<span>LIDC</span>) and <span>Image</span> <span>Database</span> <span>Resource</span> <span>Initiative</span> (<span>IDRI</span>): A completed reference database of lung nodules on <span>CT</span> scans. <em>Medical Physics</em>. 2011;38(2):915-931. doi:<a href="https://doi.org/10.1118/1.3528204">10.1118/1.3528204</a></div>
</div>
<div id="ref-bakas2017" class="csl-entry" role="listitem">
<div class="csl-left-margin">7. </div><div class="csl-right-inline"><span class="nocase">Bakas S, Akbari H, Sotiras A, et al.</span> Advancing <span>The</span> <span>Cancer</span> <span>Genome</span> <span>Atlas</span> glioma <span>MRI</span> collections with expert segmentation labels and radiomic features. <em>Scientific Data</em>. 2017;4:170117. doi:<a href="https://doi.org/10.1038/sdata.2017.117">10.1038/sdata.2017.117</a></div>
</div>
<div id="ref-menze2015" class="csl-entry" role="listitem">
<div class="csl-left-margin">8. </div><div class="csl-right-inline"><span class="nocase">Menze BH, Jakab A, Bauer S, et al.</span> The <span>Multimodal</span> <span>Brain</span> <span>Tumor</span> <span>Image</span> <span>Segmentation</span> <span>Benchmark</span> (<span>BRATS</span>). <em>IEEE Transactions on Medical Imaging</em>. 2015;34(10):1993-2024. doi:<a href="https://doi.org/10.1109/TMI.2014.2377694">10.1109/TMI.2014.2377694</a></div>
</div>
<div id="ref-jeong2023" class="csl-entry" role="listitem">
<div class="csl-left-margin">9. </div><div class="csl-right-inline"><span class="nocase">Jeong JJ, Vey BL, Bhimireddy A, et al.</span> The <span>EMory</span> <span>BrEast</span> imaging <span>Dataset</span> (<span>EMBED</span>): A racially diverse, granular dataset of 3.4 million screening and diagnostic mammographic images. <em>Radiology: Artificial Intelligence</em>. 2023;5(1):e220047. doi:<a href="https://doi.org/10.1148/ryai.220047">10.1148/ryai.220047</a></div>
</div>
<div id="ref-knoll2020" class="csl-entry" role="listitem">
<div class="csl-left-margin">10. </div><div class="csl-right-inline"><span class="nocase">Knoll F, Zbontar J, Sriram A, et al.</span> <span class="nocase">fastMRI</span>: A publicly available raw k-space and <span>DICOM</span> dataset of knee images for accelerated <span>MR</span> image reconstruction using machine learning. <em>Radiology: Artificial Intelligence</em>. 2020;2(1):e190007. doi:<a href="https://doi.org/10.1148/ryai.2020190007">10.1148/ryai.2020190007</a></div>
</div>
<div id="ref-littlejohns2020" class="csl-entry" role="listitem">
<div class="csl-left-margin">11. </div><div class="csl-right-inline"><span class="nocase">Littlejohns TJ, Holliday J, Gibson LM, et al.</span> The <span>UK</span> <span>Biobank</span> imaging enhancement of 100,000 participants: Rationale, data collection, management and future directions. <em>Nature Communications</em>. 2020;11:2624. doi:<a href="https://doi.org/10.1038/s41467-020-15948-9">10.1038/s41467-020-15948-9</a></div>
</div>
<div id="ref-meiRadImageNetOpenRadiologic2022" class="csl-entry" role="listitem">
<div class="csl-left-margin">12. </div><div class="csl-right-inline">Mei X, Liu Z, Robson PM, et al. <span>RadImageNet</span>: <span>An Open Radiologic Deep Learning Research Dataset</span> for <span>Effective Transfer Learning</span>. <em>Radiology Artificial Intelligence</em>. 2022;4(5):e210315. doi:<a href="https://doi.org/10.1148/ryai.210315">10.1148/ryai.210315</a></div>
</div>
</div>
