import { TheGuardsWalletPipeline } from '../../../theguards';

/**
 * QRL Quantum-Resistant Ledger Wallet Pipeline
 * Native Web3 transaction execution pipeline for bqrl quantum ledger stack folder.
 * Handles XMSS / QRL quantum-resistant address transactions via The Guards Scaffolding (WG-01..04).
 */
export class QrlWalletPipeline {
    /**
     * Executes a QRL / EVM transaction and AWAITS on-chain block receipt verification.
     */
    static async executeAndAwaitTransaction(req) {
        console.log(`[QrlWalletPipeline] Executing quantum-resistant transaction to ${req.to}...`);

        return TheGuardsWalletPipeline.executeAndAwaitTransaction({
            to: req.to,
            from: req.from,
            data: req.data,
            value: req.value,
            gasLimit: req.gasLimit,
            chainId: req.chainId,
            rpcUrl: req.rpcUrl || 'http://127.0.0.1:8002',
            provider: req.provider,
            confirmations: req.confirmations,
            timeoutMs: req.timeoutMs
        });
    }

    static async ensureChain(provider, chainId, rpcUrl) {
        return TheGuardsWalletPipeline.ensureChain(provider, chainId, rpcUrl);
    }
}
