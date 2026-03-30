---
layout: post
title: "2026-03-31:arxivパトロール最新30件"
date: 2026-03-31
categories: [arxiv]
---


## 注目論文

| タイトル | タグ |
|---------|------|
| [GaussianGPT: Towards Autoregressive 3D Gaussian Scene Generation](https://arxiv.org/abs/2603.26661) | `CV` |
| [VGGRPO: Towards World-Consistent Video Generation with 4D Latent Reward](https://arxiv.org/abs/2603.26599) | `CV` |
| [Weight Tying Biases Token Embeddings Towards the Output Space](https://arxiv.org/abs/2603.26663) | `NLP` |
| [The Limits of Learning from Pictures and Text: VLMs and Embodied Scene Understanding](https://arxiv.org/abs/2603.26589) | `CV` |
| [Learning to Commit: Generating Organic Pull Requests via Online Repository Memory](https://arxiv.org/abs/2603.26664) | `AI` |

---

**[GaussianGPT: Towards Autoregressive 3D Gaussian Scene Generation](https://arxiv.org/abs/2603.26661)**
`CV` · Nicolas von Lützow · 2026-03-27
> **注目理由**: 3D生成モデリングで主流の拡散モデル／フローマッチングを使わず、GPT式の次トークン予測で3Dシーンを生成する初のアーキテクチャ。Gaussian Splattingと自己回帰モデルを組み合わせた設計は、シーン補完や外部拡張など多様なタスクへの波及が期待される。

<details>
<summary>要約を読む</summary>

> 3Dシーン生成では拡散モデルが主流だったが、拡散は逐次的な修正が必要で制御しにくい問題があった。本研究では3DガウシアンをVQ-VAE（ベクトル量子化オートエンコーダ）でトークン化し、因果Transformerが次のトークンを順番に予測することで完全な3Dシーンを生成するGaussianGPTを提案した。ポイントは3D回転位置埋め込みで空間構造を捉えながら、見た目（外観）と形状（幾何学）を段階的に生成できる点だ。これにより部分的なシーンの補完、外部への拡張、温度パラメータによる多様なサンプリングが1つのモデルで実現できる。GPTスタイルの生成を3D空間に持ち込んだ点で従来とは根本的に異なるアプローチとなっている。

</details>

---

**[VGGRPO: Towards World-Consistent Video Generation with 4D Latent Reward](https://arxiv.org/abs/2603.26599)**
`CV` · Zhaochong An · 2026-03-27
> **注目理由**: 事前学習済みビデオ拡散モデルのアーキテクチャを変えずに、強化学習（GRPO）を潜在空間で適用して幾何学的一貫性を改善する手法。モデル改造なしにRL後学習で品質向上できるという設計思想は、他の制約（物理・照明など）にも応用可能。

<details>
<summary>要約を読む</summary>

> ビデオ生成AIは見た目の品質は高いが、カメラが動いたときのシーンの幾何学的一貫性（3D的な整合性）が崩れやすい問題があった。従来の解決策はモデルに追加モジュールを組み込む方法だったが、インターネット規模で事前学習した能力を損なうリスクがあった。本研究ではVGGRPO（Visual Geometry GRPO）として、モデル構造を変えず強化学習をVAEの潜在空間で行い、カメラ動作の滑らかさと幾何学的再投影整合性を報酬とする手法を提案した。潜在幾何学モデルを導入することで動的なシーン（動く物体）にも対応でき、静的シーン限定だった既存手法の限界を突破した。事前学習容量を保ちながら後学習だけで一貫性を高める設計は実用性が高い。

</details>

---

**[Weight Tying Biases Token Embeddings Towards the Output Space](https://arxiv.org/abs/2603.26663)**
`NLP` · Antonio Lopardo · 2026-03-27
> **注目理由**: LLMで広く使われる「重み共有（weight tying）」がなぜスケール時に性能劣化を引き起こすかを初めて実証的に解明。入力表現と出力予測を1つの行列で賄う設計の根本的なトレードオフを明らかにした点で、モデル設計の常識を見直させる発見。

<details>
<summary>要約を読む</summary>

> 小さなLLMではパラメータ効率のため入力埋め込み行列と出力（アンエンベディング）行列を共有する「重み共有」が広く使われているが、スケールアップ時に性能が落ちる理由は不明だった。本研究では学習初期に出力側の勾配が支配的になることで、埋め込み行列が入力表現より出力予測に最適化されてしまうことを示した。Tuned Lens（各層の内部表現を分析するツール）で検証すると、浅い層での情報処理が阻害されていることが確認された。入力側の勾配をスケーリングするだけでこのバイアスが軽減され、重み共有でも性能劣化を抑えられることを実験で示した。パラメータ数に占める埋め込み行列の割合が高い小規模LLMほど重要な知見だ。

</details>

---

**[The Limits of Learning from Pictures and Text: Vision-Language Models and Embodied Scene Understanding](https://arxiv.org/abs/2603.26589)**
`CV` · Gillian Rosenberg · 2026-03-27
> **注目理由**: 18種類のVLMを15種類のシーン理解タスクで評価し「アフォーダンス（物の使い方・操作可能性）理解には構造的な欠陥がある」と実証。プロンプト工学でも解決できず、身体的経験なしに言語と画像だけでは補えない領域があることを示した意義深い批判的研究。

<details>
<summary>要約を読む</summary>

> 「画像とテキストの統計的共起を学ぶだけで視覚認知に必要な概念知識を獲得できるか」という根本的な問いを18種類のVLMと2000人以上の人間を比較して検証した。一般知識タスクではVLMが人間レベルに近い性能を示す一方、アフォーダンスタスク（「この椅子に座れるか」「このドアをどう開けるか」）では頑健な欠陥が確認された。空間情報を明示的に与えてもプロンプトを工夫しても改善しなかったことから、この欠陥は偶発的でなく構造的なものだと結論した。画像キャプションデータにはアフォーダンスに関する言語が少ないという分析から、言語化された学習だけでは限界があり、エージェントとして3D空間を実際に操作する経験が必要だと示唆した。VLMの能力評価の枠組みを更新させる重要な研究だ。

</details>

---

**[Learning to Commit: Generating Organic Pull Requests via Online Repository Memory](https://arxiv.org/abs/2603.26664)**
`AI` · Mo Li · 2026-03-27
> **注目理由**: コーディングエージェントが「動くコード」を生成できても「そのプロジェクトらしいコード」にならない問題に正面から取り組んだ研究。過去のコミット履歴から逐次的にスキルを蒸留する「オンラインリポジトリメモリ」はAIエージェントの実用化に直結するアイデア。

<details>
<summary>要約を読む</summary>

> LLMベースのコーディングエージェントは機能的には正しいコードを書けても、プロジェクト固有の命名規則・内部APIの再利用・アーキテクチャの一貫性（「有機性」）が欠けるという課題があった。本研究では「Learning to Commit」フレームワークとして、エージェントが過去のIssueを盲目的に解決し、正解diffとの差分からプロジェクト固有のスキル（命名パターン・API使用法など）を継続的に蒸留する仕組みを提案した。新しいPRが来たとき、エージェントはこの蒸留済みスキルを参照してコード生成を行うことで、汎用パターンではなくリポジトリ固有の作法に従ったコードを生成できる。評価では機能性・コードスタイル整合性・API再利用・変更範囲の妥当性など複数軸で改善を確認した。コミット履歴が豊富なプロジェクトほど効果が高い。

</details>

---

## 全論文リスト（30件）

1. [Detailed Geometry and Appearance from Opportunistic Motion](https://arxiv.org/abs/2603.26665) `CV` · Ryosuke Hirai — 偶発的なカメラ動きから詳細な3D形状と外観を復元する手法
2. [Learning to Commit: Generating Organic Pull Requests via Online Repository Memory](https://arxiv.org/abs/2603.26664) `AI` · Mo Li — コミット履歴からスキルを蒸留してプロジェクト固有なPRを生成するエージェント
3. [Weight Tying Biases Token Embeddings Towards the Output Space](https://arxiv.org/abs/2603.26663) `NLP` · Antonio Lopardo — 重み共有がLLMの入力表現を歪める機構を実証的に解明
4. [GaussianGPT: Towards Autoregressive 3D Gaussian Scene Generation](https://arxiv.org/abs/2603.26661) `CV` · Nicolas von Lützow — 次トークン予測で3DガウシアンシーンをGPT式に生成
5. [Ruka-v2: Tendon Driven Open-Source Dexterous Hand with Wrist and Abduction for Robot Learning](https://arxiv.org/abs/2603.26660) `その他` · Xinqi Lucas — ロボット学習用オープンソース腱駆動多指ハンドの第2世代
6. [Zero-Shot Depth from Defocus](https://arxiv.org/abs/2603.26658) `CV` · Yiming Zuo — ボケ量から深度を推定するゼロショット手法
7. [Tunable Soft Equivariance with Guarantees](https://arxiv.org/abs/2603.26657) `CV` · Md Ashiqur Rahman — 保証付きの調整可能なソフト同変性を持つニューラルネット
8. [PerceptionComp: A Video Benchmark for Complex Perception-Centric Reasoning](https://arxiv.org/abs/2603.26653) `CV` · Shaoxuan Li — 複雑な知覚推論を問うビデオ理解ベンチマーク
9. [Vision2Web: A Hierarchical Benchmark for Visual Website Development with Agent Verification](https://arxiv.org/abs/2603.26648) `AI` · Zehai He — エージェントによる視覚的なWebサイト開発の階層的ベンチマーク
10. [An LP-based Sampling Policy for Multi-Armed Bandits with Side-Observations and Stochastic Availability](https://arxiv.org/abs/2603.26647) `ML` · Ashutosh Soni — 側観測と確率的可用性を持つ多腕バンディットのLP的サンプリング方策
11. [Beyond Language: Grounding Referring Expressions with Hand Pointing in Egocentric Vision](https://arxiv.org/abs/2603.26646) `CV` · Ling Li — 一人称映像で指差し動作と言語表現を組み合わせた物体参照
12. [Automatic Laplace Collapsed Sampling: Scalable Marginalisation of Latent Parameters via Automatic Differentiation](https://arxiv.org/abs/2603.26644) `ML` · Toby Lovick — 自動微分で潜在パラメータを周辺化するスケーラブルなLaplaceサンプリング
13. [Make Geometry Matter for Spatial Reasoning](https://arxiv.org/abs/2603.26639) `CV` · Shihua Zhang — 空間推論において幾何情報を効果的に活用するフレームワーク
14. [Drive-Through 3D Vehicle Exterior Reconstruction via Dynamic-Scene SfM and Distortion-Aware Gaussian Splatting](https://arxiv.org/abs/2603.26638) `CV` · Nitin Kulkarni — 走行中に車両外装を3D再構成する歪み考慮型Gaussian Splatting
15. [Machine Learning Transferability for Malware Detection](https://arxiv.org/abs/2603.26632) `ML` · César Vieira — マルウェア検知MLモデルの転移可能性を評価
16. [Context-specific Credibility-aware Multimodal Fusion with Conditional Probabilistic Circuits](https://arxiv.org/abs/2603.26629) `ML` · Pranuthi Tenali — 信頼性を考慮した条件付き確率回路によるマルチモーダル融合
17. [Benchmarking Tabular Foundation Models for Conditional Density Estimation in Regression](https://arxiv.org/abs/2603.26611) `ML` · Rafael Izbicki — 回帰タスクの条件密度推定に向けた表形式基盤モデルのベンチマーク
18. [Think over Trajectories: Leveraging Video Generation to Reconstruct GPS Trajectories from Cellular Signaling](https://arxiv.org/abs/2603.26610) `CV` · Ruixing Zhang — ビデオ生成モデルを活用して携帯信号からGPS軌跡を再構成
19. [Hardware-Aware Tensor Networks for Real-Time Quantum-Inspired Anomaly Detection at Particle Colliders](https://arxiv.org/abs/2603.26604) `ML` · Sagar Addepalli — 粒子衝突器でのリアルタイム異常検知に向けた量子インスパイアドTensor Network
20. [Sustainability Is Not Linear: Quantifying Performance, Energy, and Privacy Trade-offs in On-Device Intelligence](https://arxiv.org/abs/2603.26603) `ML` · Eziyo Ehsani — オンデバイスAIの性能・消費電力・プライバシーの非線形トレードオフを定量化
21. [VGGRPO: Towards World-Consistent Video Generation with 4D Latent Reward](https://arxiv.org/abs/2603.26599) `CV` · Zhaochong An — 潜在空間でGRPO強化学習して幾何学的一貫性のあるビデオ生成
22. [From Static to Dynamic: Exploring Self-supervised Image-to-Video Representation Transfer Learning](https://arxiv.org/abs/2603.26597) `CV` · Yang Liu — 静止画から動画への自己教師あり表現転移学習の探索
23. [Characterization and forecasting of national-scale solar power ramp events](https://arxiv.org/abs/2603.26596) `ML` · Luca Lanzilao — 国家規模の太陽光発電急変イベントの特性分析と予測
24. [PQuantML: A Tool for End-to-End Hardware-aware Model Compression](https://arxiv.org/abs/2603.26595) `ML` · Roope Niemi — ハードウェア特性を考慮したエンドツーエンドのモデル圧縮ツール
25. [Evaluating Interactive 2D Visualization as a Sample Selection Strategy for Biomedical Time-Series Data Annotation](https://arxiv.org/abs/2603.26592) `ML` · Einari Vaaras — 生体時系列アノテーション向けインタラクティブ可視化によるサンプル選択評価
26. [The Limits of Learning from Pictures and Text: Vision-Language Models and Embodied Scene Understanding](https://arxiv.org/abs/2603.26589) `CV` · Gillian Rosenberg — VLMがアフォーダンス理解で構造的欠陥を持つことを15タスクで実証
27. [From Synthetic Data to Real Restorations: Diffusion Model for Patient-specific Dental Crown Completion](https://arxiv.org/abs/2603.26588) `CV` · Dávid Pukanec — 合成データで学習した拡散モデルで患者固有の歯冠補完
28. [EnTaCs: Analyzing the Relationship Between Sentiment and Language Choice in English-Tamil Code-Switching](https://arxiv.org/abs/2603.26587) `NLP` · Paul Bontempo — 英語・タミル語コードスイッチングにおける感情と言語選択の関係分析
29. [MA-Bench: Towards Fine-grained Micro-Action Understanding](https://arxiv.org/abs/2603.26586) `CV` · Kun Li — 細粒度なマイクロアクション理解に向けたベンチマーク
30. [Scene Grounding In the Wild](https://arxiv.org/abs/2603.26584) `CV` · Tamir Cohen — 野外環境でのシーングラウンディング（言語と視覚の接地）
