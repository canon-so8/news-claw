---
layout: post
title: "arxivトレンド: 2026-03-30"
date: 2026-03-30
categories: [arxiv]
---

# 2026-03-30 18:27

# arxivトレンド論文: 2026-03-30

## 注目論文

| タイトル | タグ |
|---------|------|
| [GaussianGPT: Towards Autoregressive 3D Gaussian Scene Generation](https://arxiv.org/abs/2603.26661) | `CV` |
| [Learning to Commit: Generating Organic Pull Requests via Online Repository Memory](https://arxiv.org/abs/2603.26664) | `NLP` `AI` |
| [VGGRPO: Towards World-Consistent Video Generation with 4D Latent Reward](https://arxiv.org/abs/2603.26599) | `CV` |
| [Make Geometry Matter for Spatial Reasoning](https://arxiv.org/abs/2603.26639) | `CV` `AI` |
| [Detailed Geometry and Appearance from Opportunistic Motion](https://arxiv.org/abs/2603.26665) | `CV` |

---

**[GaussianGPT: Towards Autoregressive 3D Gaussian Scene Generation](https://arxiv.org/abs/2603.26661)**
`CV` · Nicolas von Lützow · 2026-03-27

> 3Dシーンを生成するとき、これまでは「拡散モデル（diffusion）」と呼ばれる手法が主流だった。本研究では、代わりに「次のトークンを予測する」自己回帰型のアプローチで3D Gaussianを直接生成するGaussianGPTを提案した。
> ポイントは、3Dシーンをまずスパースな3D畳み込みオートエンコーダで離散的なトークン列に圧縮し、それをCausal Transformerで順番に予測する点だ。
> この仕組みにより、「シーンの補完」や「アウトペインティング（画像の外側を埋める）」、温度パラメータによる多様な生成が自然にできるようになる。
> 自己回帰型モデルの持つ「構造の組み合わせしやすさ」と「スケーラビリティ」を3D生成に活かした意欲的な研究だ。

---

**[Learning to Commit: Generating Organic Pull Requests via Online Repository Memory](https://arxiv.org/abs/2603.26664)**
`NLP` `AI` · Mo Li · 2026-03-27

> LLMベースのコーディングエージェントは既存のベンチマークでは高得点を出せるが、実際のプロジェクトではコーディングスタイルや内部APIのルールを無視したPRを生成しがちという問題があった。
> 本研究では「Online Repository Memory」という仕組みを導入し、エージェントが過去のコミット履歴を振り返りながら「このプロジェクト独自のパターン」を学習していくフレームワーク（Learning to Commit）を提案した。
> 具体的には、昔のissueを自分で解こうとして、実際の正解diffと比べ、差分から「スキル（再利用可能なパターン）」を蓄積していく。
> 新しいPRが来たときはその蓄積されたスキルを参照するため、汎用的な事前学習の知識だけでなくプロジェクト固有の知識に基づいたコードを生成できる。

---

**[VGGRPO: Towards World-Consistent Video Generation with 4D Latent Reward](https://arxiv.org/abs/2603.26599)**
`CV` · Zhaochong An · 2026-03-27

> 大規模な動画生成モデルは見た目はきれいだが、カメラが動いたときに3D的な一貫性（「同じ物体が別角度から見ても形が崩れない」性質）を保てないことが多かった。
> 本研究ではVGGRPO（Visual Geometry GRPO）という手法を提案し、動画拡散モデルの「潜在空間（latent space）」で直接ジオメトリ（立体形状）の報酬を計算できるLatent Geometry Model（LGM）を構築した。
> 重要なのは、従来は静止シーンにしか使えなかった整合性チェックを、4D再構成モデルを使うことで動くシーンにも適用できるようにした点だ。
> カメラの動きの滑らかさと、異なる視点間の幾何学的一貫性の2種類の報酬でRLFine-tuningを行い、コストの高いVAEデコードなしに改善を実現した。

---

**[Make Geometry Matter for Spatial Reasoning](https://arxiv.org/abs/2603.26639)**
`CV` `AI` · Shihua Zhang · 2026-03-27

> VLM（視覚言語モデル）は画像と言語を組み合わせて理解できるが、「物体がどこにあるか」「空間的な関係はどうか」といった空間推論が苦手という問題があった。
> 既存研究は3D基盤モデルからの幾何学トークンをVLMに入れていたが、VLMが2D視覚情報に頼りすぎて幾何学情報をうまく使えていなかった。
> 本研究GeoSRでは、学習時に2D視覚トークンを意図的に一部マスクする「Geometry-Unleashing Masking」と、幾何学トークンの重要な箇所への貢献を増幅するゲート付きルーティングを導入した。
> 静的・動的な空間推論ベンチマークの両方でSOTAを達成した。

---

**[Detailed Geometry and Appearance from Opportunistic Motion](https://arxiv.org/abs/2603.26665)**
`CV` · Ryosuke Hirai · 2026-03-27

> 固定カメラ数台から物体の3D形状を精密に復元することは、視点の少なさから根本的に限界があった。
> 本研究では「人が物体を動かす」というごく普通の動作（椅子を移動させる、マグカップを持ち上げるなど）を利用し、固定カメラがあたかも物体の周囲を回るような仮想視点を得る「Opportunistic Motion（機会的な動き）」を活用するアイデアを提案した。
> 物体のポーズと形状推定を2D Gaussian Splattingで同時最適化しつつ、移動中の鏡面反射・拡散反射を球面調和関数空間で分離するアピアランスモデルも導入した。
> 極めて少ない固定カメラ視点でも、SOTAより大幅に精度の高い形状・外観の復元が可能になった。

---

## 全論文リスト（30件）

1. [Detailed Geometry and Appearance from Opportunistic Motion](https://arxiv.org/abs/2603.26665) `CV` · Ryosuke Hirai — 物体の偶発的な動きを利用してスパースカメラからの高精度3D復元を実現
2. [Learning to Commit: Generating Organic Pull Requests via Online Repository Memory](https://arxiv.org/abs/2603.26664) `NLP` — リポジトリのコミット履歴から学習しプロジェクト固有のPRを生成するコーディングエージェント
3. [Weight Tying Biases Token Embeddings Towards the Output Space](https://arxiv.org/abs/2603.26663) `NLP` · Antonio Lopardo — 重み共有（weight tying）が入力埋め込みよりも出力埋め込みに偏ることを実証
4. [GaussianGPT: Towards Autoregressive 3D Gaussian Scene Generation](https://arxiv.org/abs/2603.26661) `CV` · Nicolas von Lützow — 次トークン予測で3D Gaussianシーンを自己回帰的に生成するTransformerモデル
5. [Ruka-v2: Tendon Driven Open-Source Dexterous Hand with Wrist and Abduction for Robot Learning](https://arxiv.org/abs/2603.26660) `AI` · Xinqi — 手首と指の外転を備えたオープンソース腱駆動ロボットハンドの改良版
6. [Zero-Shot Depth from Defocus](https://arxiv.org/abs/2603.26658) `CV` · Yiming Zuo — フォーカススタックから深度を推定するゼロショット汎化手法FOSSAと新ベンチマークZEDD
7. [Tunable Soft Equivariance with Guarantees](https://arxiv.org/abs/2603.26657) `CV` `ML` · Md Ashiqur Rahman — 事前学習済みモデルに適用可能な等変性（equivariance）の程度を調整できる汎用フレームワーク
8. [PerceptionComp: A Video Benchmark for Complex Perception-Centric Reasoning](https://arxiv.org/abs/2603.26653) `CV` `AI` · Shaoxuan Li — 複数の時間的証拠を必要とする複雑な知覚中心の動画推論ベンチマーク
9. [Vision2Web: A Hierarchical Benchmark for Visual Website Development with Agent Verification](https://arxiv.org/abs/2603.26648) `AI` · Zehai He — 静的UI生成から全スタックWeb開発まで網羅する視覚的Webサイト開発評価ベンチマーク
10. [An LP-based Sampling Policy for Multi-Armed Bandits with Side-Observations and Stochastic Availability](https://arxiv.org/abs/2603.26647) `ML` · Ashutosh Soni — 確率的可用性を持つネットワークバンディット問題に対する線形計画ベースのUCBポリシー
11. [Beyond Language: Grounding Referring Expressions with Hand Pointing in Egocentric Vision](https://arxiv.org/abs/2603.26646) `CV` · Ling Li — 手の指差しと言語を組み合わせた一人称視点での参照表現接地の大規模データセット
12. [Automatic Laplace Collapsed Sampling: Scalable Marginalisation of Latent Parameters via Automatic Differentiation](https://arxiv.org/abs/2603.26644) `ML` · Toby Lovick — 自動微分によるラプラス近似でベイズモデルの潜在変数を効率的に周辺化するフレームワーク
13. [Make Geometry Matter for Spatial Reasoning](https://arxiv.org/abs/2603.26639) `CV` `AI` · Shihua Zhang — 幾何学トークンをVLMが積極的に活用するよう促すGeoSRフレームワーク
14. [Drive-Through 3D Vehicle Exterior Reconstruction via Dynamic-Scene SfM and Distortion-Aware Gaussian Splatting](https://arxiv.org/abs/2603.26638) `CV` · Nitin Kulkarni — ディーラーのドライブスルーで車両の高品質3D外観モデルを生成するエンドツーエンドパイプライン
15. [Machine Learning Transferability for Malware Detection](https://arxiv.org/abs/2603.26632) `ML` · César Vieira — 異なるマルウェアデータセット間でのML検出モデルの転移可能性を評価
16. [Context-specific Credibility-aware Multimodal Fusion with Conditional Probabilistic Circuits](https://arxiv.org/abs/2603.26629) `ML` · Pranuthi Tenali — インスタンスレベルで信頼性を動的評価するマルチモーダル融合フレームワークC²MF
17. [Benchmarking Tabular Foundation Models for Conditional Density Estimation in Regression](https://arxiv.org/abs/2603.26611) `ML` · Rafael Izbicki — TabPFNなど表形式基盤モデルを条件付き密度推定の観点で39データセットで体系的に評価
18. [Think over Trajectories: Leveraging Video Generation to Reconstruct GPS Trajectories from Cellular Signaling](https://arxiv.org/abs/2603.26610) `CV` `AI` · Ruixing Zhang — 携帯電話の基地局シグナルからGPSトラジェクトリを動画生成タスクとして再構成
19. [Hardware-Aware Tensor Networks for Real-Time Quantum-Inspired Anomaly Detection at Particle Colliders](https://arxiv.org/abs/2603.26604) `ML` · Sagar Addepalli — 粒子加速器でのリアルタイム異常検出に向けたFPGA実装可能な量子インスパイアードテンソルネットワーク
20. [Sustainability Is Not Linear: Quantifying Performance, Energy, and Privacy Trade-offs in On-Device Intelligence](https://arxiv.org/abs/2603.26603) `ML` · Eziyo Ehsani — スマートフォン上でのLLM実行における性能・エネルギー・プライバシーのトレードオフを実測評価
21. [VGGRPO: Towards World-Consistent Video Generation with 4D Latent Reward](https://arxiv.org/abs/2603.26599) `CV` · Zhaochong An — 潜在空間で幾何学的整合性を報酬としてRLFine-tuningする世界一貫性動画生成
22. [From Static to Dynamic: Exploring Self-supervised Image-to-Video Representation Transfer Learning](https://arxiv.org/abs/2603.26597) `CV` · Yang Liu — 画像事前学習モデルを動画タスクへ転移する際の時間的一貫性と意味的分離性のトレードオフを解消
23. [Characterization and forecasting of national-scale solar power ramp events](https://arxiv.org/abs/2603.26596) `ML` · Luca Lanzilao — 太陽光発電の急激な出力変動（ランプイベント）の国規模での特性解析と予測
24. [PQuantML: A Tool for End-to-End Hardware-aware Model Compression](https://arxiv.org/abs/2603.26595) `ML` · Roope Niemi — プルーニングと量子化を統合したハードウェア対応ニューラルネットワーク圧縮ライブラリ
25. [Evaluating Interactive 2D Visualization as a Sample Selection Strategy for Biomedical Time-Series Data Annotation](https://arxiv.org/abs/2603.26592) `ML` · Einari Vaaras — 生体時系列データのアノテーションにおける2D可視化ベースのサンプル選択戦略の比較評価
26. [The Limits of Learning from Pictures and Text: Vision-Language Models and Embodied Scene Understanding](https://arxiv.org/abs/2603.26589) `CV` · Gillian Rosenberg — VLMは一般知識タスクでは人間に近いが、身体化された場面理解（アフォーダンス）では構造的な限界がある
27. [From Synthetic Data to Real Restorations: Diffusion Model for Patient-specific Dental Crown Completion](https://arxiv.org/abs/2603.26588) `CV` · Dávid Pukanec — 合成データで学習した拡散モデルを用いた患者固有の歯冠補完
28. [EnTaCs: Analyzing the Relationship Between Sentiment and Language Choice in English-Tamil Code-Switching](https://arxiv.org/abs/2603.26587) `NLP` · Paul Bontempo — 英語・タミル語コードスイッチングにおける感情とLanguage Choiceの関係をML×統計で分析
29. [MA-Bench: Towards Fine-grained Micro-Action Understanding](https://arxiv.org/abs/2603.26586) `CV` · Kun Li — 細かな動作（マイクロアクション）理解のためのMLLM評価ベンチマークと大規模学習コーパス
30. [Scene Grounding In the Wild](https://arxiv.org/abs/2603.26584) `CV` · Tamir Cohen — Google Earth由来の擬似合成レンダリングを参照モデルとして使い、視覚的重なりなしに3D再構成を整合させる手法
