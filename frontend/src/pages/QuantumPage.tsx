/**
 * Quantum-Safe Security Page
 * ============================
 * Interactive demonstration of Post-Quantum Cryptography (PQC) capabilities.
 * Showcases CRYSTALS-Kyber and CRYSTALS-Dilithium algorithms.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Key, Lock, Unlock, Shield, Copy, Check, AlertTriangle, Info } from 'lucide-react';
import { quantumApi } from '../services/api';

export default function QuantumPage() {
  const [demoInfo, setDemoInfo] = useState<any>(null);
  const [keyPair, setKeyPair] = useState<any>(null);
  const [encryptedData, setEncryptedData] = useState<any>(null);
  const [decryptedData, setDecryptedData] = useState<string>('');
  const [signResult, setSignResult] = useState<any>(null);
  const [verifyResult, setVerifyResult] = useState<boolean | null>(null);
  const [secretResult, setSecretResult] = useState<any>(null);
  const [inputData, setInputData] = useState('');
  const [secretInput, setSecretInput] = useState('');
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [copied, setCopied] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'encrypt' | 'sign' | 'protect'>('encrypt');

  useEffect(() => {
    loadDemoInfo();
  }, []);

  const loadDemoInfo = async () => {
    try {
      const data = await quantumApi.getDemo();
      setDemoInfo(data);
    } catch (err) {
      console.error('Failed to load demo info:', err);
    }
  };

  const handleGenerateKeys = async () => {
    setLoading((prev) => ({ ...prev, keys: true }));
    try {
      const keys = await quantumApi.generateKeys('CRYSTALS-Kyber');
      setKeyPair(keys);
    } catch (err) {
      console.error('Key generation failed:', err);
    } finally {
      setLoading((prev) => ({ ...prev, keys: false }));
    }
  };

  const handleEncrypt = async () => {
    if (!inputData || !keyPair) return;
    setLoading((prev) => ({ ...prev, encrypt: true }));
    try {
      const result = await quantumApi.encrypt(inputData, keyPair.public_key);
      setEncryptedData(result);
    } catch (err) {
      console.error('Encryption failed:', err);
    } finally {
      setLoading((prev) => ({ ...prev, encrypt: false }));
    }
  };

  const handleSign = async () => {
    if (!inputData || !keyPair) return;
    setLoading((prev) => ({ ...prev, sign: true }));
    try {
      const result = await quantumApi.sign(inputData, keyPair.private_key);
      setSignResult(result);
    } catch (err) {
      console.error('Signing failed:', err);
    } finally {
      setLoading((prev) => ({ ...prev, sign: false }));
    }
  };

  const handleProtectSecret = async () => {
    if (!secretInput) return;
    setLoading((prev) => ({ ...prev, protect: true }));
    try {
      const result = await quantumApi.protectSecret(secretInput, 'demo_credential');
      setSecretResult(result);
    } catch (err) {
      console.error('Protection failed:', err);
    } finally {
      setLoading((prev) => ({ ...prev, protect: false }));
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(''), 2000);
  };

  const truncateHex = (hex: string, len: number = 32) =>
    hex.length > len * 2 ? `${hex.slice(0, len)}...${hex.slice(-16)}` : hex;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Key className="w-6 h-6 text-cyber-glow" />
          Quantum-Safe Security
        </h1>
        <p className="text-sm text-gray-400 mt-1">Post-Quantum Cryptography demonstration</p>
      </div>

      {/* Info Banner */}
      <div className="cyber-card bg-cyber-glow/5 border-cyber-glow/20">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-cyber-glow flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">About Post-Quantum Cryptography</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Current public-key cryptography (RSA, ECC) will be broken by quantum computers running Shor's algorithm.
              NIST has standardized CRYSTALS-Kyber (ML-KEM) and CRYSTALS-Dilithium (ML-DSA) as quantum-resistant
              alternatives. This module demonstrates how these algorithms protect banking credentials and security tokens.
            </p>
          </div>
        </div>
      </div>

      {/* Step 1: Generate Keys */}
      <div className="cyber-card">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <span className="w-6 h-6 bg-cyber-glow/20 rounded-full flex items-center justify-center text-xs font-bold text-cyber-glow">1</span>
          Generate Quantum-Safe Key Pair
        </h3>
        <button
          onClick={handleGenerateKeys}
          disabled={loading.keys}
          className="cyber-button-primary"
        >
          {loading.keys ? 'Generating...' : 'Generate Kyber Key Pair'}
        </button>

        {keyPair && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 space-y-3">
            <div className="p-3 bg-cyber-dark rounded-lg border border-cyber-border">
              <p className="text-[10px] text-gray-500 uppercase mb-1">Algorithm</p>
              <p className="text-sm text-cyber-glow font-medium">{keyPair.algorithm}</p>
            </div>
            <div className="p-3 bg-cyber-dark rounded-lg border border-cyber-border">
              <div className="flex items-center justify-between mb-1">
                <p className="text-[10px] text-gray-500 uppercase">Public Key</p>
                <button onClick={() => copyToClipboard(keyPair.public_key, 'pub')} className="text-gray-500 hover:text-cyber-glow">
                  {copied === 'pub' ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                </button>
              </div>
              <p className="text-xs text-gray-300 font-mono break-all">{truncateHex(keyPair.public_key, 40)}</p>
            </div>
            <div className="p-3 bg-cyber-dark rounded-lg border border-cyber-border">
              <div className="flex items-center justify-between mb-1">
                <p className="text-[10px] text-gray-500 uppercase">Private Key</p>
                <button onClick={() => copyToClipboard(keyPair.private_key, 'priv')} className="text-gray-500 hover:text-cyber-glow">
                  {copied === 'priv' ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                </button>
              </div>
              <p className="text-xs text-gray-300 font-mono break-all">{truncateHex(keyPair.private_key, 40)}</p>
            </div>
            <p className="text-[10px] text-yellow-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              In production, private keys are stored in HSMs and never exposed.
            </p>
          </motion.div>
        )}
      </div>

      {/* Step 2: Operations */}
      {keyPair && (
        <div className="cyber-card">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <span className="w-6 h-6 bg-cyber-glow/20 rounded-full flex items-center justify-center text-xs font-bold text-cyber-glow">2</span>
            Encrypt / Sign / Protect
          </h3>

          {/* Tabs */}
          <div className="flex gap-2 mb-4">
            {[
              { key: 'encrypt', label: 'Encrypt Data', icon: Lock },
              { key: 'sign', label: 'Digital Signature', icon: Shield },
              { key: 'protect', label: 'Protect Secret', icon: Key },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  activeTab === tab.key ? 'bg-cyber-glow/20 text-cyber-glow border border-cyber-glow/30' : 'bg-cyber-dark text-gray-400 border border-cyber-border hover:text-gray-300'
                }`}
              >
                <tab.icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Encrypt Tab */}
          {activeTab === 'encrypt' && (
            <div className="space-y-3">
              <input
                type="text" value={inputData}
                onChange={(e) => setInputData(e.target.value)}
                placeholder="Enter data to encrypt (e.g., API key, password)..."
                className="cyber-input"
              />
              <button onClick={handleEncrypt} disabled={!inputData || loading.encrypt} className="cyber-button-primary">
                {loading.encrypt ? 'Encrypting...' : 'Encrypt with Kyber'}
              </button>
              {encryptedData && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-3 bg-cyber-dark rounded-lg border border-cyber-border space-y-2">
                  <p className="text-[10px] text-green-400 uppercase font-semibold">Encrypted Successfully</p>
                  <div>
                    <p className="text-[10px] text-gray-500">Ciphertext</p>
                    <p className="text-xs text-gray-300 font-mono break-all">{truncateHex(encryptedData.ciphertext, 30)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">Encapsulated Key</p>
                    <p className="text-xs text-gray-300 font-mono break-all">{truncateHex(encryptedData.encapsulated_key, 30)}</p>
                  </div>
                  <p className="text-[10px] text-gray-500">Algorithm: {encryptedData.algorithm}</p>
                </motion.div>
              )}
            </div>
          )}

          {/* Sign Tab */}
          {activeTab === 'sign' && (
            <div className="space-y-3">
              <input
                type="text" value={inputData}
                onChange={(e) => setInputData(e.target.value)}
                placeholder="Enter message to sign..."
                className="cyber-input"
              />
              <button onClick={handleSign} disabled={!inputData || loading.sign} className="cyber-button-primary">
                {loading.sign ? 'Signing...' : 'Sign with Dilithium'}
              </button>
              {signResult && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-3 bg-cyber-dark rounded-lg border border-cyber-border space-y-2">
                  <p className="text-[10px] text-green-400 uppercase font-semibold">Signature Created</p>
                  <div>
                    <p className="text-[10px] text-gray-500">Signature</p>
                    <p className="text-xs text-gray-300 font-mono break-all">{truncateHex(signResult.signature, 30)}</p>
                  </div>
                  <p className="text-[10px] text-gray-500">Algorithm: {signResult.algorithm}</p>
                </motion.div>
              )}
            </div>
          )}

          {/* Protect Secret Tab */}
          {activeTab === 'protect' && (
            <div className="space-y-3">
              <input
                type="password" value={secretInput}
                onChange={(e) => setSecretInput(e.target.value)}
                placeholder="Enter a secret to protect (e.g., API key, DB password)..."
                className="cyber-input"
              />
              <button onClick={handleProtectSecret} disabled={!secretInput || loading.protect} className="cyber-button-primary">
                {loading.protect ? 'Protecting...' : 'Protect Secret with PQC'}
              </button>
              {secretResult && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-3 bg-cyber-dark rounded-lg border border-cyber-border space-y-2">
                  <p className="text-[10px] text-green-400 uppercase font-semibold">Secret Protected</p>
                  <div>
                    <p className="text-[10px] text-gray-500">Encrypted Secret</p>
                    <p className="text-xs text-gray-300 font-mono break-all">{truncateHex(secretResult.encrypted_secret, 30)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">Purpose</p>
                    <p className="text-xs text-gray-300">{secretResult.purpose}</p>
                  </div>
                  <p className="text-[10px] text-gray-500">Algorithm: {secretResult.algorithm}</p>
                </motion.div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Algorithm Info Cards */}
      {demoInfo && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(demoInfo.algorithms || {}).map(([name, info]: [string, any]) => (
            <motion.div key={name} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="cyber-card">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Key className="w-4 h-4 text-cyber-glow" />
                {name}
              </h3>
              <div className="space-y-2">
                <div><p className="text-[10px] text-gray-500 uppercase">Type</p><p className="text-xs text-gray-300">{info.type}</p></div>
                <div><p className="text-[10px] text-gray-500 uppercase">Standard</p><p className="text-xs text-gray-300">{info.standard}</p></div>
                <div><p className="text-[10px] text-gray-500 uppercase">Use Case</p><p className="text-xs text-gray-300">{info.use_case}</p></div>
                <div><p className="text-[10px] text-gray-500 uppercase">Security Basis</p><p className="text-xs text-gray-300">{info.security_basis}</p></div>
                <div>
                  <p className="text-[10px] text-gray-500 uppercase">Key Sizes</p>
                  <div className="space-y-1 mt-1">
                    {Object.entries(info.key_sizes || {}).map(([size, desc]) => (
                      <div key={size} className="flex items-center gap-2">
                        <span className="text-xs text-cyber-glow font-mono">{size}</span>
                        <span className="text-[10px] text-gray-500">{desc as string}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Banking Use Cases */}
      {demoInfo?.banking_use_cases && (
        <div className="cyber-card">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-cyber-glow" />
            Banking Use Cases for PQC
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {demoInfo.banking_use_cases.map((useCase: string, i: number) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-cyber-dark rounded-lg">
                <div className="w-1.5 h-1.5 bg-cyber-glow rounded-full mt-1.5 flex-shrink-0"></div>
                <p className="text-xs text-gray-300">{useCase}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
