---
title: "Genomics Is Not NLP: A Field Guide for ML Scientists"
date: 2026-06-03
permalink: /posts/2026/06/genomics-vs-nlp/
repro_url: https://github.com/josephrich98/joseph_rich_blog/tree/main/posts/2026-06-03-genomics-vs-nlp
excerpt: "A field guide for ML scientists moving into genomics and transcriptomics: why DNA only looks like text, why the whole species is one near-duplicate corpus, how regulation defeats the context window, the biology you cannot skip, why the molecule you sequence is not the one that acts, and what the famous foundation models do and don't solve."
tags:
  - machine learning
  - genomics
  - transcriptomics
  - natural language processing
  - computational biology
toc: true
comments: true
---
<!-- Generated from posts/2026-06-03-genomics-vs-nlp/main.md by scripts/sync_posts.py. Do not edit here; edit the source and re-commit. -->


Before diving into a discussion of genomics and natural language processing (NLP), we should review a basic primer of molecular biology. For the biologists out there, forgive me for making some oversimplifications. This field is much richer than can be fit in one paragraph! And for the computer scientists out there, there really is more to biology than dissecting frogs and annotating oversaturated printouts of the endoplasmic reticulum. 

## Molecular biology primer
DNA is the "blueprint" of the human body that holds our genetic code. Every cell in a specific organism possesses identical DNA (barring mutations that accumulate over a person‘s life); it is regulation of this DNA that leads to differences between cell types (eg neuron vs. liver cell). DNA is a large molecule comprised of nucleotides — small chemical subunits that can be abstracted as "letters". These four nucleotides are adenine (A), cytosine (C), guanine (G), and thymine (T). DNA is packaged into chromosomes. Humans have 46 chromosomes and are diploid — our chromosomes come in pairs, where we inherit half of our chromosomes from our mom and half from our dad. The chromosomes are numbered 1-22 (autosomes — descending order of length) and X/Y (sex chromosomes). The human genome contains ~3.2 billion nucleotides in total. The central dogma of molecular biology describes the fundamental role of DNA: DNA is transcribed into messenger RNA (mRNA), a form of ribonucleic acid (RNA), and mRNA is translated into protein. Only ~1–2% of DNA encodes mRNA; the rest of DNA is involved in regulation of gene expression, transcription into non-coding RNA, structural roles (such as centromeres and telomeres), has uncharacterized function, or may serve no function at all. mRNA is also comprised of nucleotides like DNA, and is grouped into triplets called codons during translation, where each codon encodes an amino acid. Amino acids are the subunit of proteins. There are 20 amino acids (the memorization of which is a rite of passage for every biochemistry student), each characterized by different chemical structures and properties (e.g., polarity, acidity, size, disulfide-bond potential, phosphorylation potential). As there are 4^3 = 64 possible nucleotide combinations in a codon, the existence of only 20 amino acids implies that the genetic code is degenerate: 1-4 codons will encode the same amino acid. Proteins do the work of the cell — they catalyze reactions, communicate signals, transport molecules, build structures, and much more. Effectively, DNA is relevant only insofar that it encodes mRNA, which itself encodes protein — DNA molecules themselves serve essentially no role in the human body outside of this function. 

## DNA and NLP similarities and differences
At first glance, genomics looks like a direct analog to natural language processing. And in some respects, it is. Both the English language and the genetic code share a small finite alphabet — English has 26 letters, and DNA has four nucleotides (ACGT). Both have an exponentially large number of units that can be formed by unique permutations of this alphabet — English groups letters into words, and DNA groups nucleotides into genes. The two vocabulary sizes are comparable — there are ~20,000 words in the English language and ~20,000 genes encoded in the human body.

But there are also some crucial differences that must be addressed. For instance, English words are often within a narrow length range of 2 to 10 characters. Genes, however, range anywhere between 1,000 to 1,000,000 nucleotides. Changing an English sentence with even a single letter substitution is guaranteed to change the meaning of a sentence, as the similarity in meaning between words holds minimal correlation with similarity in structure. With DNA, some base substitutions are completely invisible, some have modest effects on outcome, and some are catastrophic. Mutations outside gene-coding regions nearly always have no effect. Mutations within gene-coding regions generally only have an effect if they cause a change in amino acid, and especially if they significantly change the chemical properties of the amino acid. Mutations are significant when they result in a change in protein folding structure, which can lead to protein instability or loss of ligand specificity. 

DNA and English text also have different numbers of hierarchical groupings. As discussed earlier, nucleotides can be thought of as analogous to letters, and genes can be thought of as analogous to words. Carrying forward this analogy, each chromosome or entire human genome could be thought of as analogous to a document. However, there is no analogue to a "sentence" for DNA. Each "document" would simply read as a list of words used exactly one time, likely ordered based on their position in the genome — an order that has little functional significance. Or, perhaps, different conventions can be applied to DNA. For instance, an alternative representation would be to represent DNA codons as letters, rather than individual nucleotides, which would create a 64 character alphabet rather than a four character alphabet. This would pose its own challenges, however, such as the degeneracy of the DNA code (up to four codons can encode the same amino acid, with the last nucleotide often being flexible) and the questionable relevance of codon-tokenization in non-coding regions (where transcription does not occur). Or, alternatively yet again, if we stick with nucleotides as letters, then these codons or other k-mers (subsequences of length k) could represent words, and genes could represent sentences. But this still runs into the problem of high "sentence" similarity and "document" structure.

Any two English sentences or documents will contain vastly different structure. Some documents might be one sentence, while others might be hundreds of pages long. The lengths of sentences and vocabulary used can vary widely. For text classification, such as sentiment analysis, the entire body of text must be analyzed, as each portion can contribute to the meaning of the text as a whole. In contrast, DNA has a highly consistent structure between individuals. Any two individuals are ~99.9% identical. Of the ~3.2 billion nucleotides in the human genome, only ~10 million nucleotides have substantial (common) variation across the human population <sup><a href="#ref-auton2015" role="doc-biblioref">1</a></sup>. This shallow diversity is due to a population bottleneck approximately 50,000 years ago which restricted our genetic ancestors to approximately 10,000 individuals. Most of these variants have a most common form, which can be collected into what is called a reference genome^1. In addition to these ~10 million sites of possible variation, each person has ~70 *de novo* mutations that are specific to them <sup><a href="#ref-kong2012" role="doc-biblioref">2</a></sup>, and any given cell may accumulate up to several thousand somatic mutations over the person's life <sup><a href="#ref-blokzijl2016" role="doc-biblioref">3</a></sup>. This means that any artificial intelligence (AI) model that ingests the entire 3.2 billion nucleotide sequence is exerting a lot of unnecessary energy, as most sites are essentially guaranteed to match the reference genome. There are benefits to working with raw DNA sequences as well. The simplicity of the input data, the direct analog to natural language, and the ability to maintain the full context of DNA that is especially relevant for tasks such as mutation effect prediction. But this trade-off is unique to genomics data and should be intentionally considered by the machine learning practitioner.

![**Figure 1**](/images/posts/2026-06-03-genomics-vs-nlp/corpus_redundancy_a.png)

**Figure 1**: Two members of the human species are near-duplicates. The fraction of positions that differ between two sequences, on a log scale: two humans differ at only $$\sim 10^{-3}$$ of positions and human versus chimpanzee at $$\sim 10^{-2}$$, whereas two random DNA strings differ at $$0.75$$ and two unrelated English documents at essentially every position. The within-species genomic "corpus" is roughly a thousandfold more redundant than text.

## Sources of genomic data
Genomics data can come from multiple sources. These include whole genome sequencing (WGS; sequencing the entire genome), whole exome sequencing (WES; sequencing only the gene-encoding regions of the genome), bulk RNA-sequencing (bulk RNA-seq; sequencing all expressed RNA), and single-cell RNA sequencing (scRNA-seq; sequencing RNA at single-cell resolution). These sequencing machines have ~99–99.9% per-base accuracy. When only mildly confident about the detected nucleotide, the machine may report a lowercase letter. When entirely unconfident, the machine may report an "N". How to handle these additional characters is a design decision in any tokenizer.

The protocol to sequence genomic data depends on the assay and technology, but they all share the isolation of genetic material, decomposition into small regions generally between 75-150 nucleotides (reads), amplification by polymerase chain reaction (PCR), and sequence readout. The reads (FASTQ file) are usually mapped to the reference genome (FASTA file) to produce a genome alignment (BAM, or Binary Alignment Map, file). For DNA, the variants can be extracted in a VCF (Variant Call Format) file. For RNA data, the count of each gene can be stored in a count matrix, where each row represents a sample (bulk RNA-seq) or cell (single-cell RNA-seq), and each column represents a gene.

## DNA, RNA, and protein
I mentioned earlier that proteins are the real molecule of interest in the human body, so why do we measure RNA at all rather than measuring protein directly? One of the main reasons is that protein sequencing technology has simply lagged behind nucleotide sequencing technology in cost. The underlying assumption is that RNA levels correlate strongly with protein levels, so the former can be used as a proxy for the latter. However, this may be a stronger assumption than most would like to believe. Across many careful studies, the correlation between a gene’s mRNA level and its protein level is moderate at best — typically a Spearman ρ in the 0.4-0.6 range, and lower still when you look at changes over time rather than steady-state across genes. Schwanhäusser and colleagues found mRNA explained well under half the variance in protein abundance <sup><a href="#ref-schwanhausser2011" role="doc-biblioref">4</a></sup>; Vogel and Marcotte, Liu, Beyer and Aebersold, and Buccitelli and Selbach all converge on the same message — translation rates, protein half-lives, and post-translational regulation drive a large share of protein levels that mRNA simply does not see <sup><a href="#ref-vogel2012" role="doc-biblioref">5</a>–<a href="#ref-buccitelli2020" role="doc-biblioref">7</a></sup>. Edfors and colleagues showed the relationship is gene-specific <sup><a href="#ref-edfors2016" role="doc-biblioref">8</a></sup>: each gene has roughly its own mRNA-to-protein conversion factor, so a single global model is wrong per gene. Figure 2 shows the consequence in real data — even at the optimistic end of that range, knowing a gene’s mRNA leaves its protein level uncertain across a wide band.

![**Figure 2**](/images/posts/2026-06-03-genomics-vs-nlp/proxy_scatter.png)

**Figure 2**: mRNA is a noisy proxy for protein. Real per-gene mRNA and protein copy numbers in mouse NIH3T3 fibroblasts (Schwanhäusser et al. 2011; $$n=4{,}309$$ genes; Pearson $$r=0.62$$ on log abundances). The red line is the best fit; even so, protein scatters across two to three orders of magnitude at any given mRNA level, because translation and degradation are not observed in the RNA.

## Popular datasets
Below is a set of some of the most popular public datasets in genomics. File sizes can be quite large — for WGS, FASTQ files are often around 100-200GB, BAM files are 30-100GB, and VCF files are 1-10GB. However, as described earlier, much of this information represents redundancy with the reference genome, and individuals are often the unit of interest when training AI models rather than nucleotides, so cohort sizes in the thousands-hundreds of thousands range is often fairly small for modern AI. Additionally, most data are collected on healthy individuals or individuals with cancer, so it is difficult to study other diseases because public datasets will be quite small (if available at all). And any data collected from a single institution or region will have batch effects, limiting generalizability to other populations. 

| Resource | What it is | Assay | Reported scale | Ref. |
| -------- | ---------- | ----- | -------------- | ---- |
| **1000 Genomes** | Reference catalogue of human variation | WGS, WES | 2,504 individuals, 26 populations; ~88M variants | <sup><a href="#ref-auton2015" role="doc-biblioref">1</a></sup> |
| **gnomAD** | Aggregated exomes + genomes; constraint metrics | WES, WGS | 125,748 exomes + 15,708 genomes (v2) | <sup><a href="#ref-karczewski2020" role="doc-biblioref">9</a></sup> |
| **UK Biobank** | Population cohort, genotype + deep phenotype | Array, WES, WGS | ~500,000 participants | <sup><a href="#ref-bycroft2018" role="doc-biblioref">10</a></sup> |
| **TCGA** | Pan-cancer tumor/normal multi-omics | WXS, WGS, bulk RNA-seq, WSI | ~11,000 tumors, 33 cancer types | <sup><a href="#ref-weinstein2013" role="doc-biblioref">11</a></sup> |
| **GTEx** | Genetic regulation of expression across tissues | bulk RNA-seq, WGS | 17,382 RNA-seq samples, 54 tissues, 948 donors | <sup><a href="#ref-gtex2020" role="doc-biblioref">12</a></sup> |
| **ENCODE** | Functional/regulatory element annotation | ChIP-seq, ATAC, DNase, RNA-seq | Genome-wide assays across many cell types | <sup><a href="#ref-encode2012" role="doc-biblioref">13</a></sup> |
| **GENCODE** | Reference gene/transcript annotation | Annotation | ~20,000 coding genes; >200,000 transcripts | <sup><a href="#ref-frankish2021" role="doc-biblioref">14</a></sup> |
| **Geuvadis** | RNA-seq paired to 1000 Genomes genotypes | bulk RNA-seq | 462 individuals, 5 populations | <sup><a href="#ref-lappalainen2013" role="doc-biblioref">15</a></sup> |
| **Tabula Sapiens** | Multi-organ single-cell atlas | scRNA-seq | ~500,000 cells, ~24 tissues | <sup><a href="#ref-tabulasapiens2022" role="doc-biblioref">16</a></sup> |
| **CZ CELLxGENE Discover** | Aggregated, standardized single-cell expression atlas | scRNA-seq | >90M cells across thousands of datasets | <sup><a href="#ref-cellxgene2023" role="doc-biblioref">17</a></sup> |
| **Human Cell Atlas** | Cross-tissue single-cell reference of every cell type | scRNA-seq | Tens of millions of cells across many tissues | <sup><a href="#ref-regev2017" role="doc-biblioref">18</a></sup> |
| **10x Genomics Datasets** | Vendor-released public single-cell/-nucleus datasets | scRNA-seq | Hundreds of datasets across tissues | <sup><a href="#ref-zheng2017" role="doc-biblioref">19</a></sup> |
| **T2T-CHM13** | First complete (telomere-to-telomere) human genome | WGS (long-read) | 1 gapless assembly | <sup><a href="#ref-nurk2022" role="doc-biblioref">20</a></sup> |

*Assay abbreviations: WGS = whole-genome sequencing; WES/WXS = whole-exome sequencing; bulk RNA-seq = bulk RNA sequencing; scRNA-seq = single-cell RNA sequencing; Array = genotyping microarray; WSI = whole-slide imaging; ChIP-seq = chromatin immunoprecipitation sequencing; ATAC = assay for transposase-accessible chromatin; DNase = DNase I hypersensitivity sequencing.*

Two structural problems run underneath these numbers.

## How real models approach this
We've talked a lot about how genetic material can be represented as text for AI models. But what is actually done in practice? Here are a few notable examples.
- **AlphaFold2** (Jumper et al.<sup><a href="#ref-jumper2021" role="doc-biblioref">21</a></sup>) predicts protein three-dimensional (3D) structure from amino-acid sequence at near-experimental accuracy — arguably the field's defining success. It takes a protein's amino-acid sequence, together with a multiple-sequence alignment of evolutionarily related proteins and any available structural templates, and predicts the 3D coordinates of every atom. The sequence is treated as a string over the fixed 20-letter amino-acid alphabet — each residue is mapped to a learned embedding rather than an arbitrary text token — and much of the biological signal comes from the MSA, whose column-wise evolutionary covariation encodes which residues are likely to contact one another in 3D. Protein folding is a problem that possesses multiple attributes that make it an ideal candidate for AI. The 3D structure depends entirely on the discrete amino acid sequence itself, without dependencies from other parts of the genome or cell state broadly. There are over 200,000 experimentally determined protein structures with resolved amino-acid sequences across humans and model organisms <sup><a href="#ref-berman2000" role="doc-biblioref">22</a></sup>, representing a dataset that is large enough for supervised learning. And amino acids have biochemical properties that enable logical verification of predicted results to an extent.
- **Enformer** (Avsec et al.<sup><a href="#ref-avsec2021" role="doc-biblioref">23</a></sup>) and **AlphaGenome** (DeepMind, 2025<sup><a href="#ref-avsec2025" role="doc-biblioref">24</a></sup>) attack the *cis*-regulatory problem head-on, predicting expression and chromatin readouts from sequence across ~200 kilobases and up to 1 megabase windows respectively. They are the state of the art on long-range *cis* effects — and structurally blind to *trans* regulation that acts through diffusible proteins or other chromosomes. Both take a one-hot-encoded DNA sequence — a long genomic window centered on the region of interest — and predict thousands of functional genomic and epigenomic tracks (expression, chromatin accessibility, histone marks, and more) along that window. Here the alphabet is simply the four DNA bases (A/C/G/T): each position becomes a 4-dimensional one-hot vector, so — unlike a text model with a learned subword vocabulary — there is no tokenization step at all, and biology enters through the fixed base alphabet and the reverse-complement symmetry the architectures are built to respect (a sequence and its complementary strand should give the same prediction). 
- **DNABERT** (Ji et al.<sup><a href="#ref-ji2021" role="doc-biblioref">25</a></sup>), the **Nucleotide Transformer** (Dalla-Torre et al.<sup><a href="#ref-dallatorre2024" role="doc-biblioref">26</a></sup>), and **Evo** (Nguyen et al.<sup><a href="#ref-nguyen2024" role="doc-biblioref">27</a></sup>) are DNA "language models" — masked or autoregressive pre-training over genomic sequence, transferred to downstream tasks. Each tokenizes raw nucleotide sequence — overlapping k-mers for DNABERT, fixed non-overlapping k-mer tokens for the Nucleotide Transformer, and single-nucleotide (byte-level) tokens for Evo — and learns representations by predicting masked or next tokens over large genomic corpora. The vocabulary is built from the four nucleotides rather than natural-language words, and the differing tokenizations are attempts to package that four-letter alphabet into biologically meaningful units: k-mers approximate short motifs or codon-like chunks, while single-base tokens keep every nucleotide addressable at the cost of longer sequences. 
- **scGPT** (Cui et al.<sup><a href="#ref-cui2024" role="doc-biblioref">28</a></sup>) and **Geneformer** (Theodoris et al.<sup><a href="#ref-theodoris2023" role="doc-biblioref">29</a></sup>) bring the foundation-model recipe to single-cell transcriptomics, learning representations of cell state from large RNA-expression atlases. These approaches do not take in raw sequencing reads as input, but rather the processed count matrices. Consequently the "alphabet" is not sequence at all but the roughly 20,000 genes — each gene is a token, and its expression level is encoded either by binning the count into discrete value tokens (scGPT) or by ranking genes from most to least expressed within a cell (Geneformer), so the biology is carried by which genes are on and their relative levels rather than by any letter sequence.

## Conclusion
There have been exciting developments in genomics AI, and there is much to be done moving forward. ~40% of variants in cancer cases are still classified as variants of unknown significance <sup><a href="#ref-mellgard2024" role="doc-biblioref">30</a></sup>. When analyzing a cancer patient's mutations, it is still often impossible to distinguish the driver mutation from passenger mutations. The role of genomics outside of cancer and well-characterized genes characterized by single mutation/gene events is minimal in clinical practice. A single human scRNA-seq experiment often has thousands of cells, and tens of thousands of genes. In an atlas comprised of dozens or hundreds of datasets, there can be millions of cells, with various sources of batch effects. Continuing to develop models that can make sense of these data will be critical for advancing genomics research.

1. The human reference genome disproportionately represents individuals of European ancestry, as these are the most widely available genomic data. Recent efforts have been made to create pan-genomes that better represent global diversity, most notably the Human Pangenome Reference Consortium's draft reference assembled from 47 genetically diverse individuals <sup><a href="#ref-liao2023" role="doc-biblioref">31</a></sup>.

# References

<div id="refs" class="references csl-bib-body" role="list">
<div id="ref-auton2015" class="csl-entry" role="listitem">
<div class="csl-left-margin">1. </div><div class="csl-right-inline"><span class="nocase">Auton A, Brooks LD, Durbin RM, et al.</span> A global reference for human genetic variation. <em>Nature</em>. 2015;526(7571):68-74. doi:<a href="https://doi.org/10.1038/nature15393">10.1038/nature15393</a></div>
</div>
<div id="ref-kong2012" class="csl-entry" role="listitem">
<div class="csl-left-margin">2. </div><div class="csl-right-inline"><span class="nocase">Kong A, Frigge ML, Masson G, et al.</span> Rate of de novo mutations and the importance of father’s age to disease risk. <em>Nature</em>. 2012;488(7412):471-475. doi:<a href="https://doi.org/10.1038/nature11396">10.1038/nature11396</a></div>
</div>
<div id="ref-blokzijl2016" class="csl-entry" role="listitem">
<div class="csl-left-margin">3. </div><div class="csl-right-inline"><span class="nocase">Blokzijl F, Ligt J de, Jager M, et al.</span> Tissue-specific mutation accumulation in human adult stem cells during life. <em>Nature</em>. 2016;538(7624):260-264. doi:<a href="https://doi.org/10.1038/nature19768">10.1038/nature19768</a></div>
</div>
<div id="ref-schwanhausser2011" class="csl-entry" role="listitem">
<div class="csl-left-margin">4. </div><div class="csl-right-inline"><span class="nocase">Schwanhäusser B, Busse D, Li N, et al.</span> Global quantification of mammalian gene expression control. <em>Nature</em>. 2011;473(7347):337-342. doi:<a href="https://doi.org/10.1038/nature10098">10.1038/nature10098</a></div>
</div>
<div id="ref-vogel2012" class="csl-entry" role="listitem">
<div class="csl-left-margin">5. </div><div class="csl-right-inline">Vogel C, Marcotte EM. Insights into the regulation of protein abundance from proteomic and transcriptomic analyses. <em>Nature Reviews Genetics</em>. 2012;13(4):227-232. doi:<a href="https://doi.org/10.1038/nrg3185">10.1038/nrg3185</a></div>
</div>
<div id="ref-liu2016" class="csl-entry" role="listitem">
<div class="csl-left-margin">6. </div><div class="csl-right-inline">Liu Y, Beyer A, Aebersold R. On the dependency of cellular protein levels on <span class="nocase">mRNA</span> abundance. <em>Cell</em>. 2016;165(3):535-550. doi:<a href="https://doi.org/10.1016/j.cell.2016.03.014">10.1016/j.cell.2016.03.014</a></div>
</div>
<div id="ref-buccitelli2020" class="csl-entry" role="listitem">
<div class="csl-left-margin">7. </div><div class="csl-right-inline">Buccitelli C, Selbach M. <span class="nocase">mRNAs</span>, proteins and the emerging principles of gene expression control. <em>Nature Reviews Genetics</em>. 2020;21(10):630-644. doi:<a href="https://doi.org/10.1038/s41576-020-0258-4">10.1038/s41576-020-0258-4</a></div>
</div>
<div id="ref-edfors2016" class="csl-entry" role="listitem">
<div class="csl-left-margin">8. </div><div class="csl-right-inline"><span class="nocase">Edfors F, Danielsson F, Hallström BM, et al.</span> Gene-specific correlation of <span>RNA</span> and protein levels in human cells and tissues. <em>Molecular Systems Biology</em>. 2016;12(10):883. doi:<a href="https://doi.org/10.15252/msb.20167144">10.15252/msb.20167144</a></div>
</div>
<div id="ref-karczewski2020" class="csl-entry" role="listitem">
<div class="csl-left-margin">9. </div><div class="csl-right-inline"><span class="nocase">Karczewski KJ, Francioli LC, Tiao G, et al.</span> The mutational constraint spectrum quantified from variation in 141,456 humans. <em>Nature</em>. 2020;581(7809):434-443. doi:<a href="https://doi.org/10.1038/s41586-020-2308-7">10.1038/s41586-020-2308-7</a></div>
</div>
<div id="ref-bycroft2018" class="csl-entry" role="listitem">
<div class="csl-left-margin">10. </div><div class="csl-right-inline"><span class="nocase">Bycroft C, Freeman C, Petkova D, et al.</span> The <span>UK</span> <span>Biobank</span> resource with deep phenotyping and genomic data. <em>Nature</em>. 2018;562(7726):203-209. doi:<a href="https://doi.org/10.1038/s41586-018-0579-z">10.1038/s41586-018-0579-z</a></div>
</div>
<div id="ref-weinstein2013" class="csl-entry" role="listitem">
<div class="csl-left-margin">11. </div><div class="csl-right-inline"><span class="nocase">Weinstein JN, Collisson EA, Mills GB, et al.</span> The <span>Cancer</span> <span>Genome</span> <span>Atlas</span> <span>Pan-Cancer</span> analysis project. <em>Nature Genetics</em>. 2013;45(10):1113-1120. doi:<a href="https://doi.org/10.1038/ng.2764">10.1038/ng.2764</a></div>
</div>
<div id="ref-gtex2020" class="csl-entry" role="listitem">
<div class="csl-left-margin">12. </div><div class="csl-right-inline">GTEx Consortium. The <span>GTEx</span> <span>Consortium</span> atlas of genetic regulatory effects across human tissues. <em>Science</em>. 2020;369(6509):1318-1330. doi:<a href="https://doi.org/10.1126/science.aaz1776">10.1126/science.aaz1776</a></div>
</div>
<div id="ref-encode2012" class="csl-entry" role="listitem">
<div class="csl-left-margin">13. </div><div class="csl-right-inline">ENCODE Project Consortium. An integrated encyclopedia of <span>DNA</span> elements in the human genome. <em>Nature</em>. 2012;489(7414):57-74. doi:<a href="https://doi.org/10.1038/nature11247">10.1038/nature11247</a></div>
</div>
<div id="ref-frankish2021" class="csl-entry" role="listitem">
<div class="csl-left-margin">14. </div><div class="csl-right-inline"><span class="nocase">Frankish A, Diekhans M, Jungreis I, et al.</span> <span>GENCODE</span> 2021. <em>Nucleic Acids Research</em>. 2021;49(D1):D916-D923. doi:<a href="https://doi.org/10.1093/nar/gkaa1087">10.1093/nar/gkaa1087</a></div>
</div>
<div id="ref-lappalainen2013" class="csl-entry" role="listitem">
<div class="csl-left-margin">15. </div><div class="csl-right-inline"><span class="nocase">Lappalainen T, Sammeth M, Friedländer MR, et al.</span> Transcriptome and genome sequencing uncovers functional variation in humans. <em>Nature</em>. 2013;501(7468):506-511. doi:<a href="https://doi.org/10.1038/nature12531">10.1038/nature12531</a></div>
</div>
<div id="ref-tabulasapiens2022" class="csl-entry" role="listitem">
<div class="csl-left-margin">16. </div><div class="csl-right-inline">Tabula Sapiens Consortium. The <span>Tabula</span> <span>Sapiens</span>: A multiple-organ, single-cell transcriptomic atlas of humans. <em>Science</em>. 2022;376(6594):eabl4896. doi:<a href="https://doi.org/10.1126/science.abl4896">10.1126/science.abl4896</a></div>
</div>
<div id="ref-cellxgene2023" class="csl-entry" role="listitem">
<div class="csl-left-margin">17. </div><div class="csl-right-inline"><span class="nocase">Abdulla S, Aevermann B, Assis P, et al.</span> <span>CZ</span> <span>CELLxGENE</span> <span>Discover</span>: A single-cell data platform for scalable exploration, analysis and modeling of aggregated data. <em>bioRxiv</em>. Published online 2023. doi:<a href="https://doi.org/10.1101/2023.10.30.563174">10.1101/2023.10.30.563174</a></div>
</div>
<div id="ref-regev2017" class="csl-entry" role="listitem">
<div class="csl-left-margin">18. </div><div class="csl-right-inline"><span class="nocase">Regev A, Teichmann SA, Lander ES, et al.</span> The <span>Human</span> <span>Cell</span> <span>Atlas</span>. <em>eLife</em>. 2017;6:e27041. doi:<a href="https://doi.org/10.7554/eLife.27041">10.7554/eLife.27041</a></div>
</div>
<div id="ref-zheng2017" class="csl-entry" role="listitem">
<div class="csl-left-margin">19. </div><div class="csl-right-inline"><span class="nocase">Zheng GXY, Terry JM, Belgrader P, et al.</span> Massively parallel digital transcriptional profiling of single cells. <em>Nature Communications</em>. 2017;8:14049. doi:<a href="https://doi.org/10.1038/ncomms14049">10.1038/ncomms14049</a></div>
</div>
<div id="ref-nurk2022" class="csl-entry" role="listitem">
<div class="csl-left-margin">20. </div><div class="csl-right-inline"><span class="nocase">Nurk S, Koren S, Rhie A, et al.</span> The complete sequence of a human genome. <em>Science</em>. 2022;376(6588):44-53. doi:<a href="https://doi.org/10.1126/science.abj6987">10.1126/science.abj6987</a></div>
</div>
<div id="ref-jumper2021" class="csl-entry" role="listitem">
<div class="csl-left-margin">21. </div><div class="csl-right-inline"><span class="nocase">Jumper J, Evans R, Pritzel A, et al.</span> Highly accurate protein structure prediction with <span>AlphaFold</span>. <em>Nature</em>. 2021;596(7873):583-589. doi:<a href="https://doi.org/10.1038/s41586-021-03819-2">10.1038/s41586-021-03819-2</a></div>
</div>
<div id="ref-berman2000" class="csl-entry" role="listitem">
<div class="csl-left-margin">22. </div><div class="csl-right-inline"><span class="nocase">Berman HM, Westbrook J, Feng Z, et al.</span> The <span>Protein</span> <span>Data</span> <span>Bank</span>. <em>Nucleic Acids Research</em>. 2000;28(1):235-242. doi:<a href="https://doi.org/10.1093/nar/28.1.235">10.1093/nar/28.1.235</a></div>
</div>
<div id="ref-avsec2021" class="csl-entry" role="listitem">
<div class="csl-left-margin">23. </div><div class="csl-right-inline"><span class="nocase">Avsec Ž, Agarwal V, Visentin D, et al.</span> Effective gene expression prediction from sequence by integrating long-range interactions. <em>Nature Methods</em>. 2021;18(10):1196-1203. doi:<a href="https://doi.org/10.1038/s41592-021-01252-x">10.1038/s41592-021-01252-x</a></div>
</div>
<div id="ref-avsec2025" class="csl-entry" role="listitem">
<div class="csl-left-margin">24. </div><div class="csl-right-inline"><span class="nocase">Avsec Ž, Latysheva N, Cheng J, et al.</span> <span>AlphaGenome</span>: Advancing regulatory variant effect prediction with a unified <span>DNA</span> sequence model. <em>bioRxiv</em>. Published online 2025. doi:<a href="https://doi.org/10.1101/2025.06.25.661532">10.1101/2025.06.25.661532</a></div>
</div>
<div id="ref-ji2021" class="csl-entry" role="listitem">
<div class="csl-left-margin">25. </div><div class="csl-right-inline">Ji Y, Zhou Z, Liu H, Davuluri RV. <span>DNABERT</span>: Pre-trained <span>Bidirectional</span> <span>Encoder</span> <span>Representations</span> from <span>Transformers</span> model for <span class="nocase">DNA-language</span> in genome. <em>Bioinformatics</em>. 2021;37(15):2112-2120. doi:<a href="https://doi.org/10.1093/bioinformatics/btab083">10.1093/bioinformatics/btab083</a></div>
</div>
<div id="ref-dallatorre2024" class="csl-entry" role="listitem">
<div class="csl-left-margin">26. </div><div class="csl-right-inline"><span class="nocase">Dalla-Torre H, Gonzalez L, Mendoza-Revilla J, et al.</span> Nucleotide <span>Transformer</span>: Building and evaluating robust foundation models for human genomics. <em>Nature Methods</em>. 2024;22(2):287-297. doi:<a href="https://doi.org/10.1038/s41592-024-02523-z">10.1038/s41592-024-02523-z</a></div>
</div>
<div id="ref-nguyen2024" class="csl-entry" role="listitem">
<div class="csl-left-margin">27. </div><div class="csl-right-inline"><span class="nocase">Nguyen E, Poli M, Durrant MG, et al.</span> Sequence modeling and design from molecular to genome scale with <span>Evo</span>. <em>Science</em>. 2024;386(6723):eado9336. doi:<a href="https://doi.org/10.1126/science.ado9336">10.1126/science.ado9336</a></div>
</div>
<div id="ref-cui2024" class="csl-entry" role="listitem">
<div class="csl-left-margin">28. </div><div class="csl-right-inline"><span class="nocase">Cui H, Wang C, Maan H, et al.</span> <span class="nocase">scGPT</span>: Toward building a foundation model for single-cell multi-omics using generative <span>AI</span>. <em>Nature Methods</em>. 2024;21(8):1470-1480. doi:<a href="https://doi.org/10.1038/s41592-024-02201-0">10.1038/s41592-024-02201-0</a></div>
</div>
<div id="ref-theodoris2023" class="csl-entry" role="listitem">
<div class="csl-left-margin">29. </div><div class="csl-right-inline"><span class="nocase">Theodoris CV, Xiao L, Chopra A, et al.</span> Transfer learning enables predictions in network biology. <em>Nature</em>. 2023;618(7965):616-624. doi:<a href="https://doi.org/10.1038/s41586-023-06139-9">10.1038/s41586-023-06139-9</a></div>
</div>
<div id="ref-mellgard2024" class="csl-entry" role="listitem">
<div class="csl-left-margin">30. </div><div class="csl-right-inline"><span class="nocase">Mellgard GS, Atabek Z, LaRose M, et al.</span> Variants of uncertain significance in precision oncology: Nuance or nuisance? <em>The Oncologist</em>. 2024;29(8):641-644. doi:<a href="https://doi.org/10.1093/oncolo/oyae135">10.1093/oncolo/oyae135</a></div>
</div>
<div id="ref-liao2023" class="csl-entry" role="listitem">
<div class="csl-left-margin">31. </div><div class="csl-right-inline"><span class="nocase">Liao W-W, Asri M, Ebler J, et al.</span> A draft human pangenome reference. <em>Nature</em>. 2023;617(7960):312-324. doi:<a href="https://doi.org/10.1038/s41586-023-05896-x">10.1038/s41586-023-05896-x</a></div>
</div>
</div>
