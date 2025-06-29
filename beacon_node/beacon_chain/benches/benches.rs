use std::sync::Arc;

use beacon_chain::{
    data_column_verification::validate_data_column_sidecar_for_gossip,
    kzg_utils::blobs_to_data_column_sidecars,
    observed_data_sidecars::DoNotObserve,
    test_utils::{BeaconChainHarness, EphemeralHarnessType},
};
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use types::{
    beacon_block_body::KzgCommitments, BeaconBlock, BeaconBlockDeneb, Blob, BlobsList, ChainSpec,
    EmptyBlock, EthSpec, ForkName, KzgProofs, MainnetEthSpec, SignedBeaconBlock,
};
use bls::Signature;
use kzg::{KzgCommitment, KzgProof};

type E = MainnetEthSpec;
type T = EphemeralHarnessType<E>;

fn create_test_block_and_blobs(
    num_of_blobs: usize,
    spec: &ChainSpec,
) -> (SignedBeaconBlock<E>, BlobsList<E>, KzgProofs<E>) {
    let mut block = BeaconBlock::Deneb(BeaconBlockDeneb::empty(spec));
    let mut body = block.body_mut();
    let blob_kzg_commitments = body.blob_kzg_commitments_mut().unwrap();
    *blob_kzg_commitments =
        KzgCommitments::<E>::new(vec![KzgCommitment::empty_for_testing(); num_of_blobs]).unwrap();

    let signed_block = SignedBeaconBlock::from_block(block, Signature::empty());

    let blobs = (0..num_of_blobs)
        .map(|_| Blob::<E>::default())
        .collect::<Vec<_>>()
        .into();
    let proofs = vec![KzgProof::empty(); num_of_blobs * spec.number_of_columns as usize].into();

    (signed_block, blobs, proofs)
}

fn setup_test_harness() -> BeaconChainHarness<T> {
    let spec = ForkName::Fulu.make_genesis_spec(E::default_spec());
    BeaconChainHarness::builder(E::default())
        .spec(Arc::new(spec))
        .deterministic_keypairs(64)
        .fresh_ephemeral_store()
        .mock_execution_layer()
        .build()
}

fn bench_validate_data_column_sidecar_for_gossip(c: &mut Criterion) {
    let harness = setup_test_harness();
    let chain = &harness.chain;
    let spec = &chain.spec;
    let kzg = &chain.kzg;

    let mut group = c.benchmark_group("validate_data_column_sidecar_for_gossip");
    
    for blob_count in [1, 5, 10, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 35, 40, 50] {
        let (signed_block, blobs, proofs) = create_test_block_and_blobs(blob_count, spec);
        
        let column_sidecars = blobs_to_data_column_sidecars(
            &blobs.iter().collect::<Vec<_>>(),
            proofs.to_vec(),
            &signed_block,
            kzg,
            spec,
        )
        .unwrap();

        if let Some(data_column) = column_sidecars.first() {
            let data_column = Arc::new(data_column.clone());
            let subnet = 0u64;
            
            group.bench_with_input(
                BenchmarkId::new("blobs", blob_count),
                &blob_count,
                |b, _| {
                    b.iter(|| {
                        let _ = black_box(validate_data_column_sidecar_for_gossip::<_, DoNotObserve>(
                            (*data_column).clone(),
                            subnet,
                            chain,
                        ));
                    })
                },
            );
        }
    }
    
    group.finish();
}

criterion_group!(benches, bench_validate_data_column_sidecar_for_gossip);
criterion_main!(benches);