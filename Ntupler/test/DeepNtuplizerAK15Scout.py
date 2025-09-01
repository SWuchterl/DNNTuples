import FWCore.ParameterSet.Config as cms

# ---------------------------------------------------------
from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('analysis')

options.outputFile = 'output.root'
options.inputFiles = 'file:///eos/cms/store/mc/RunIII2024Summer24MiniAODv6/GluGluH-Hto2C_Par-M-125_TuneCP5_13p6TeV_powhegMINLO-pythia8/MINIAODSIM/150X_mcRun3_2024_realistic_v2_ext1-v2/100000/78849373-9e62-4381-aff6-dcb6f83a1910.root' ## H->WH/ZH->aaxx
# options.inputFiles = 'file:/afs/cern.ch/user/c/coli/miniv6.root'

options.maxEvents = -1

options.register('skipEvents', 0, VarParsing.multiplicity.singleton, VarParsing.varType.int, "skip N events")
options.register('inputDataset',
                 '',
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.string,
                 "Input dataset")
options.register('isTrainSample', True, VarParsing.multiplicity.singleton,
                 VarParsing.varType.bool, "if the sample is used for training")
# special output configs
options.register('addMET', False, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "add MET vars to output file")
options.register('addLowLevel', True, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "add low-level vars to output file")
options.register('isMDTagger', True, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "use MD tagger categorisation")
options.register('keepAllEvents', False, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "keep all events for QCD and ttbar when creating inference dataset (isTrainSample=False)")
options.register('adhocFixMode', 0, VarParsing.multiplicity.singleton, VarParsing.varType.int, "ad-hoc fix mode")

options.parseArguments()

# test command: cmsRun DeepNtuplizerAK15Scout.py maxEvents=100 isTrainSample=1

globalTagMap = {
    '24' : '150X_mcRun3_2024_realistic_v1',
}
era = '24'

## current workflow: only run interactively
assert options.inputDataset == '' and len(options.inputFiles) == 1, 'Only run interactively with file len=1'
print("Running", options.inputFiles)

# ---------------------------------------------------------
process = cms.Process("DNNFiller")

process.load('FWCore.MessageService.MessageLogger_cfi')
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

process.options = cms.untracked.PSet(
    allowUnscheduled=cms.untracked.bool(True),
    wantSummary=cms.untracked.bool(False)
)

print('Using output file ' + options.outputFile)

process.TFileService = cms.Service("TFileService",
                                   fileName=cms.string(options.outputFile))

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(options.maxEvents))

process.source = cms.Source('PoolSource',
                            fileNames=cms.untracked.vstring(options.inputFiles),
                            skipEvents=cms.untracked.uint32(options.skipEvents)
                            )
# ---------------------------------------------------------
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.EventContent.EventContent_cff")
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
process.load('PhysicsTools.NanoAOD.custom_run3scouting_cff')
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, globalTagMap[era], '')
print('Using global tag', process.GlobalTag.globaltag)

# !!! set `useReclusteredJets = True ` if you need to recluster jets (e.g., to adopt a new Puppi tune) !!!
useReclusteredJets = False
jetR = 1.5

assert useReclusteredJets == False, 'Reclustering jets is not supported in this version yet'
srcJets = cms.InputTag('slimmedJetsAK8') # use default fatjet collection in MiniAOD

## ========== load the scouting AK15 jet reclustering task ========== ##
## https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_0/PhysicsTools/NanoAOD/python/custom_run3scouting_cff.py
from PhysicsTools.NanoAOD.run3scouting_cff import *
# process.scoutingFatPFJet15ReclusterTask = cms.Task(
#     scoutingPFCandidate, # translate to reco::PFCandidate, used as input
#     scoutingFatPFJet15Recluster, # jet clustering
#     scoutingFatPFJet15ReclusterParticleNetJetTagInfos, scoutingFatPFJet15ReclusterParticleNetJetTags, # jet tagging
#     scoutingFatPFJet15ReclusterSoftDrop, scoutingFatPFJet15ReclusterSoftDropMass, # softdrop mass
#     scoutingFatPFJet15ReclusterParticleNetJetTagInfos, scoutingFatPFJet15ReclusterParticleNetMassRegressionJetTags, # regressed mass
#     scoutingFatPFJet15ReclusterEcfNbeta1, scoutingFatPFJet15ReclusterNjettiness, # substructure variables
#     # scoutingFatPFJet15ReclusterTable
# )
# process.scoutingFatPFJet15Match = cms.EDProducer("JetMatcherDRAllowEmpty",
#     source = cms.InputTag("slimmedJetsAK8"),
#     matched = cms.InputTag("scoutingFatPFJet15Recluster")
# )
# process.scoutingFatPFJet15ReclusterTask.add(process.scoutingFatPFJet15Match)





process.scoutingFatPFJet15ReclusterMatchGenExtensionTable = process.scoutingFatPFJetReclusterMatchGenExtensionTable.clone(
    externalVariables = cms.PSet(
        genJetAK8Idx = cms.PSet(
            doc = cms.string('gen jet idx'),
            precision = cms.int32(-1),
            src = cms.InputTag("scoutingFatPFJet15ReclusterMatchGen"),
            type = cms.string('int')
        )
    ),
    name = cms.string('ScoutingFatPFJet15Recluster'),
    src = cms.InputTag("scoutingFatPFJet15Recluster"),
)
del process.scoutingFatPFJetReclusterMatchGenExtensionTable

process.scoutingFatPFJet15ReclusterMatchGen = process.scoutingFatPFJetReclusterMatchGen.clone(
    distMax = cms.double(1.5),
    matched = cms.InputTag("slimmedGenJetsAK8"),
    src = cms.InputTag("scoutingFatPFJet15Recluster"),
)
del process.scoutingFatPFJetReclusterMatchGen

# add ak15
process.scoutingFatPFJet15ReclusterMatchGenExtensionTask = cms.Task(
    process.scoutingFatPFJet15ReclusterMatchGen,
    process.scoutingFatPFJet15ReclusterMatchGenExtensionTable
)


process.scoutingFatPFJet15Recluster = process.scoutingFatPFJetRecluster.clone(
    rParam = cms.double(1.5),
)
del process.scoutingFatPFJetRecluster

process.scoutingFatPFJet15ReclusterEcfNbeta1 = process.scoutingFatPFJetReclusterEcfNbeta1.clone(
    src = cms.InputTag("scoutingFatPFJet15Recluster"),
)
del process.scoutingFatPFJetReclusterEcfNbeta1

process.scoutingFatPFJet15ReclusterGlobalParticleTransformerJetTagInfos = process.scoutingFatPFJetReclusterGlobalParticleTransformerJetTagInfos.clone(
    jets = cms.InputTag("scoutingFatPFJet15Recluster"),
    jet_radius = cms.double(1.5),
)
del process.scoutingFatPFJetReclusterGlobalParticleTransformerJetTagInfos

process.scoutingFatPFJet15ReclusterGlobalParticleTransformerJetTags = process.scoutingFatPFJetReclusterGlobalParticleTransformerJetTags.clone(
    jets = cms.InputTag("scoutingFatPFJet15Recluster"),
    src = cms.InputTag("scoutingFatPFJet15ReclusterGlobalParticleTransformerJetTagInfos")
)
del process.scoutingFatPFJetReclusterGlobalParticleTransformerJetTags

process.scoutingFatPFJet15ReclusterNjettiness = process.scoutingFatPFJetReclusterNjettiness.clone(
    R0 = cms.double(1.5),
    src = cms.InputTag("scoutingFatPFJet15Recluster"),
)
del process.scoutingFatPFJetReclusterNjettiness

process.scoutingFatPFJet15ReclusterParticleNetJetTagInfos = process.scoutingFatPFJetReclusterParticleNetJetTagInfos.clone(
    jets = cms.InputTag("scoutingFatPFJet15Recluster"),
    jet_radius = cms.double(1.5),
)
del process.scoutingFatPFJetReclusterParticleNetJetTagInfos

process.scoutingFatPFJet15ReclusterParticleNetJetTags = process.scoutingFatPFJetReclusterParticleNetJetTags.clone(
    jets = cms.InputTag("scoutingFatPFJet15Recluster"),
    src = cms.InputTag("scoutingFatPFJet15ReclusterParticleNetJetTagInfos")
)
del process.scoutingFatPFJetReclusterParticleNetJetTags

process.scoutingFatPFJet15ReclusterParticleNetMassRegressionJetTags = process.scoutingFatPFJetReclusterParticleNetMassRegressionJetTags.clone(
    jets = cms.InputTag("scoutingFatPFJet15Recluster"),
    src = cms.InputTag("scoutingFatPFJet15ReclusterParticleNetJetTagInfos")
)
del process.scoutingFatPFJetReclusterParticleNetMassRegressionJetTags

process.scoutingFatPFJet15ReclusterSoftDrop = process.scoutingFatPFJetReclusterSoftDrop.clone(
    R0 = cms.double(1.5),
    rParam = cms.double(1.5),
)
del process.scoutingFatPFJetReclusterSoftDrop

process.scoutingFatPFJet15ReclusterSoftDropMass = process.scoutingFatPFJetReclusterSoftDropMass.clone(
    distMax = cms.double(1.5),
    matched = cms.InputTag("scoutingFatPFJet15ReclusterSoftDrop"),
    src = cms.InputTag("scoutingFatPFJet15Recluster"),
)
del process.scoutingFatPFJetReclusterSoftDropMass

process.scoutingFatPFJet15ReclusterTask = cms.Task(
    process.scoutingFatPFJet15Recluster,
    process.scoutingFatPFJet15ReclusterEcfNbeta1,
    process.scoutingFatPFJet15ReclusterGlobalParticleTransformerJetTagInfos,
    process.scoutingFatPFJet15ReclusterGlobalParticleTransformerJetTags,
    process.scoutingFatPFJet15ReclusterNjettiness,
    process.scoutingFatPFJet15ReclusterParticleNetJetTagInfos,
    process.scoutingFatPFJet15ReclusterParticleNetJetTags,
    process.scoutingFatPFJet15ReclusterParticleNetMassRegressionJetTags,
    process.scoutingFatPFJet15ReclusterSoftDrop,
    process.scoutingFatPFJet15ReclusterSoftDropMass,
    # process.scoutingFatPFJet15ReclusterTable,
    process.scoutingPFCandidate
)
del process.scoutingFatPFJetReclusterTable
process.scoutingNanoTaskMC.remove(process.scoutingFatPFJetReclusterMatchGenExtensionTask)
del process.scoutingFatPFJetReclusterMatchGenExtensionTask



process.scoutingFatPFJet15Match = cms.EDProducer("JetMatcherDRAllowEmpty",
    source = cms.InputTag("slimmedJetsAK8"),
    matched = cms.InputTag("scoutingFatPFJet15Recluster")
)
process.scoutingFatPFJet15ReclusterTask.add(process.scoutingFatPFJet15Match)



# process.scoutingNanoTaskCommon = cms.Task(process.scoutingElectronTableTask, process.scoutingFatPFJetReclusterTask, process.scoutingMETTable, process.scoutingMuonDisplacedVertexTableTask, process.scoutingMuonTableTask, process.scoutingPFJetReclusterTask, process.scoutingPFJetTable, process.scoutingPhotonTable, process.scoutingPrimaryVertexTable, process.scoutingRhoTable)

# process.scoutingNanoTaskCommon.add(process.scoutingFatPFJet15ReclusterTask)

# process.scoutingNanoTaskMC = cms.Task(process.puTable, process.scoutingFatPFJetReclusterMatchGenExtensionTask, process.scoutingPFJetReclusterMatchGenExtensionTask)

# process.scoutingNanoTaskMC.add(process.scoutingFatPFJet15ReclusterMatchGenExtensionTask)


## ========== end of scouting AK15 jet reclustering task ========== ##


# !!! as a starting point of Nano v15 routines: do not do custom tagger inference !!!
doCustomTaggerInference = False

# from dnntuple v9: infer the new tagger so as to store the hidden layer scores in a special branch jet_custom_discs
btagDiscriminatorsCustomSaveAsCompact = []
btagDiscriminatorsCustomSaveAsSeparate = []

if doCustomTaggerInference:
    from DeepNTuples.Ntupler.jetTools import updateJetCollection # use custom updataJetCollection with new tagger configs included
    from DeepNTuples.Ntupler.hwwTagger.pfMassDecorrelatedDeepHWWV1_cff import _pfMassDecorrelatedDeepHWWV1JetTagsAll
    from DeepNTuples.Ntupler.hwwTagger.pfMassDecorrelatedInclParticleTransformerV2_cff import _pfMassDecorrelatedInclParticleTransformerV2HidLayerJetTagsProbsHidNeurons
    from DeepNTuples.Ntupler.hwwTagger.pfMassDecorrelatedInclParticleTransformerV1_cff import _pfMassDecorrelatedInclParticleTransformerV1JetTagsAll
    from DeepNTuples.Ntupler.hwwTagger.pfMassDecorrelatedInclParticleTransformerV3_cff import _pfMassDecorrelatedInclParticleTransformerV3HidLayerJetTagsAll
    _pfMassDecorrelatedInclParticleTransformerV1JetTagsSelected = [disc for disc in _pfMassDecorrelatedInclParticleTransformerV1JetTagsAll if 'hidNeuron' not in disc]
    _pfMassDecorrelatedInclParticleTransformerV2HidLayerJetTagsProbsRawScoresSelected = [
        'pfMassDecorrelatedInclParticleTransformerV2HidLayerJetTags:' + flav_name for flav_name in [
            'probTopbWcs', 'probTopbWqq', 'probTopbWc', 'probTopbWs', 'probTopbWq', 'probTopbWev', 'probTopbWmv', 'probTopbWtauev', 'probTopbWtaumv', 'probTopbWtauhv',
            'probTopWcs', 'probTopWqq', 'probTopWev', 'probTopWmv', 'probTopWtauev', 'probTopWtaumv', 'probTopWtauhv',
            'probHbb', 'probHcc', 'probHss', 'probHqq', 'probHbc', 'probHcs', 'probHgg', 'probHee', 'probHmm', 'probHtauhtaue', 'probHtauhtaum', 'probHtauhtauh',
            'probHWWcscs', 'probHWWcsqq', 'probHWWqqqq', 'probHWWcsc', 'probHWWcss', 'probHWWcsq', 'probHWWqqc', 'probHWWqqs', 'probHWWqqq',
            'probHWWcsev', 'probHWWqqev', 'probHWWcsmv', 'probHWWqqmv', 'probHWWcstauev', 'probHWWqqtauev', 'probHWWcstaumv', 'probHWWqqtaumv', 'probHWWcstauhv', 'probHWWqqtauhv',
            'probQCDbb', 'probQCDcc', 'probQCDb', 'probQCDc', 'probQCDothers', 
            'resonanceMassCorr', 'visiableMassCorr'
            ]
        ]
    _pfMassDecorrelatedInclParticleTransformerV3HidLayerJetTagsSelected = [disc for disc in _pfMassDecorrelatedInclParticleTransformerV3HidLayerJetTagsAll if 'hidNeuron' not in disc]
    btagDiscriminatorsCustomSaveAsSeparate += _pfMassDecorrelatedDeepHWWV1JetTagsAll + _pfMassDecorrelatedInclParticleTransformerV1JetTagsSelected + _pfMassDecorrelatedInclParticleTransformerV2HidLayerJetTagsProbsRawScoresSelected + _pfMassDecorrelatedInclParticleTransformerV3HidLayerJetTagsSelected

# ---------------------------------------------------------
from PhysicsTools.PatAlgos.tools.helpers import getPatAlgosToolsTask, addToProcessAndTask
patTask = getPatAlgosToolsTask(process)

from RecoJets.JetProducers.ak8GenJets_cfi import ak8GenJets
from RecoJets.Configuration.GenJetParticles_cff import genParticlesForJetsNoNu
process.ak15GenJetsWithNu = ak8GenJets.clone(
    src='packedGenParticles',
    rParam=cms.double(jetR),
    jetPtMin=100.0
)
process.ak15GenJetsWithNuSoftDrop = process.ak15GenJetsWithNu.clone(
    useSoftDrop=cms.bool(True),
    zcut=cms.double(0.1),
    beta=cms.double(0.0),
    R0=cms.double(jetR),
    useExplicitGhosts=cms.bool(True)
)
process.packedGenParticlesForJetsNoNu = genParticlesForJetsNoNu.clone(
    src='packedGenParticles'
)
process.ak15GenJetsNoNu = process.ak15GenJetsWithNu.clone(
    src='packedGenParticlesForJetsNoNu' # using packedGenParticles with no neutrinos as input
)
process.ak15GenJetsNoNuSoftDrop = process.ak15GenJetsWithNuSoftDrop.clone(
    src='packedGenParticlesForJetsNoNu'
)
process.ak15GenJetsWithNuMatch = cms.EDProducer("GenJetMatcher",  # cut on deltaR; pick best by deltaR
                                               src=srcJets,  # RECO jets (any View<Jet> is ok)
                                               # GEN jets  (must be GenJetCollection)
                                               matched=cms.InputTag("ak15GenJetsWithNu"),
                                               mcPdgId=cms.vint32(),  # n/a
                                               mcStatus=cms.vint32(),  # n/a
                                               checkCharge=cms.bool(False),  # n/a
                                               maxDeltaR=cms.double(jetR),  # Minimum deltaR for the match
                                               # maxDPtRel   = cms.double(3.0),                  # Minimum deltaPt/Pt for the match (not used in GenJetMatcher)
                                               # Forbid two RECO objects to match to the same GEN object
                                               resolveAmbiguities=cms.bool(True),
                                               # False = just match input in order; True = pick lowest deltaR pair first
                                               resolveByMatchQuality=cms.bool(False),
                                               )
process.ak15GenJetsWithNuSoftDropMatch = cms.EDProducer("GenJetMatcher",  # cut on deltaR; pick best by deltaR
                                                       src=srcJets,  # RECO jets (any View<Jet> is ok)
                                                       # GEN jets  (must be GenJetCollection)
                                                       matched=cms.InputTag("ak15GenJetsWithNuSoftDrop"),
                                                       mcPdgId=cms.vint32(),  # n/a
                                                       mcStatus=cms.vint32(),  # n/a
                                                       checkCharge=cms.bool(False),  # n/a
                                                       maxDeltaR=cms.double(jetR),  # Minimum deltaR for the match
                                                       # maxDPtRel   = cms.double(3.0),                  # Minimum deltaPt/Pt for the match (not used in GenJetMatcher)
                                                       # Forbid two RECO objects to match to the same GEN object
                                                       resolveAmbiguities=cms.bool(True),
                                                       # False = just match input in order; True = pick lowest deltaR pair first
                                                       resolveByMatchQuality=cms.bool(False),
                                                       )
process.ak15GenJetsNoNuMatch = process.ak15GenJetsWithNuMatch.clone(matched=cms.InputTag("ak15GenJetsNoNu"))
process.ak15GenJetsNoNuSoftDropMatch = process.ak15GenJetsWithNuSoftDropMatch.clone(matched=cms.InputTag("ak15GenJetsNoNuSoftDrop"))

process.genJetTask = cms.Task(
    process.ak15GenJetsWithNu,
    process.ak15GenJetsWithNuMatch,
    process.ak15GenJetsWithNuSoftDrop,
    process.ak15GenJetsWithNuSoftDropMatch,
    process.packedGenParticlesForJetsNoNu,
    process.ak15GenJetsNoNu,
    process.ak15GenJetsNoNuMatch,
    process.ak15GenJetsNoNuSoftDrop,
    process.ak15GenJetsNoNuSoftDropMatch,
)

# DeepNtuplizer
process.load("DeepNTuples.Ntupler.DeepNtuplizer_cfi")
process.deepntuplizer.jets = srcJets
process.deepntuplizer.useReclusteredJets = useReclusteredJets

from RecoBTag.ONNXRuntime.pfParticleNet_cff import _pfParticleNetJetTagsAll as pfParticleNetJetTagsAll
from RecoBTag.ONNXRuntime.pfParticleNet_cff import _pfParticleNetMassRegressionOutputs as pfParticleNetMassRegressionOutputs
from RecoBTag.ONNXRuntime.pfParticleNetFromMiniAODAK8_cff import _pfParticleNetFromMiniAODAK8JetTagsAll as pfParticleNetFromMiniAODAK8JetTagsAll
from RecoBTag.ONNXRuntime.pfGlobalParticleTransformerAK8_cff import _pfGlobalParticleTransformerAK8JetTagsAll as pfGlobalParticleTransformerAK8JetTagsAll
process.deepntuplizer.bDiscriminators = pfParticleNetJetTagsAll + pfParticleNetMassRegressionOutputs + pfParticleNetFromMiniAODAK8JetTagsAll + \
                                        [d for d in pfGlobalParticleTransformerAK8JetTagsAll if 'hidNeuron' not in d] + \
                                        btagDiscriminatorsCustomSaveAsSeparate
process.deepntuplizer.bDiscriminatorsCompactSave = btagDiscriminatorsCustomSaveAsCompact

process.deepntuplizer.genJetsWithNuMatch = 'ak15GenJetsWithNuMatch'
process.deepntuplizer.genJetsWithNuSoftDropMatch = 'ak15GenJetsWithNuSoftDropMatch'
process.deepntuplizer.genJetsNoNuMatch = 'ak15GenJetsNoNuMatch'
process.deepntuplizer.genJetsNoNuSoftDropMatch = 'ak15GenJetsNoNuSoftDropMatch'

# add scouting jet match
process.deepntuplizer.scoutingJetMatch = 'scoutingFatPFJet15Match'

# determine sample type with inputFiles name
_inputfile = options.inputFiles[0]
process.deepntuplizer.isQCDSample = '/QCD_' in _inputfile
process.deepntuplizer.isTTBarSample = 'tott' in _inputfile.lower() or 'ttbar' in _inputfile.lower()
process.deepntuplizer.isHVV2DVarMassSample = '2DMesh' in _inputfile
process.deepntuplizer.isPythia = 'pythia' in _inputfile.lower()
process.deepntuplizer.isHerwig = 'herwig' in _inputfile.lower()
# note: MG can be interfaced w/ either pythia or herwig
process.deepntuplizer.isMadGraph = 'madgraph' in _inputfile.lower()

process.deepntuplizer.isTrainSample = options.isTrainSample

# special output configs
process.deepntuplizer.addMET = options.addMET
process.deepntuplizer.addLowLevel = options.addLowLevel
process.deepntuplizer.isMDTagger = options.isMDTagger
process.deepntuplizer.keepAllEvents = options.keepAllEvents
process.deepntuplizer.adhocFixMode = options.adhocFixMode
#==============================================================================================================================#
process.p = cms.Path(process.deepntuplizer)
process.p.associate(patTask)
process.p.associate(process.genJetTask)
process.p.associate(process.scoutingFatPFJet15ReclusterTask)

if process.scoutingFatPFJetReclusterTask:
# process.scoutingNanoTaskCommon = cms.Task(
#     process.scoutingElectronTableTask,
#     process.scoutingFatPFJetReclusterTask,
#     process.scoutingMETTable,
#     process.scoutingMuonDisplacedVertexTableTask,
#     process.scoutingMuonTableTask,
#     process.scoutingPFJetReclusterTask,
#     process.scoutingPFJetTable,
#     process.scoutingPhotonTable,
#     process.scoutingPrimaryVertexTable,
# process.scoutingRhoTable)
    process.scoutingNanoTaskCommon.remove(process.scoutingFatPFJetReclusterTask)
    del process.scoutingFatPFJetReclusterTask

# open("debug_dump_AK15.py", "w").write(process.dumpPython())