#!/usr/bin/env python3
"""
Universal EEG Loader for OpenBCI Data
Handles .mat (MATLAB) and .edf (European Data Format) files
"""

import numpy as np
import mne
from pathlib import Path


class UniversalEEGLoader:
    """
    Loads EEG data from .mat or .edf files and converts to standard format
    """
    
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.raw = None
        self.data = None
        self.sampling_rate = None
        self.n_channels = None
        self.channel_names = None
        
    def load(self):
        """
        Automatically detect format and load
        """
        print(f"\n{'='*70}")
        print(f"Loading: {self.filepath.name}")
        print(f"{'='*70}")
        
        file_ext = self.filepath.suffix.lower()
        
        if file_ext == '.edf':
            return self._load_edf()
        elif file_ext == '.mat':
            return self._load_mat()
        else:
            print(f"✗ Unsupported format: {file_ext}")
            return False
    
    def _load_edf(self):
        """
        Load EDF format files
        """
        print("Format: EDF (European Data Format)")
        
        try:
            self.raw = mne.io.read_raw_edf(
                self.filepath,
                preload=True,
                verbose=False
            )
            
            self._extract_metadata()
            print("✓ EDF file loaded successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error loading EDF: {e}")
            return False
    
    def _load_mat(self):
        """
        Load MATLAB format files (handles v7 and v7.3)
        """
        print("Format: MATLAB .mat")
        
        # Try scipy first (v7 and earlier)
        try:
            import scipy.io as sio
            
            mat = sio.loadmat(
                self.filepath,
                struct_as_record=False,
                squeeze_me=True
            )
            
            print("  Loaded with scipy.io (MATLAB v7)")
            return self._extract_from_scipy_mat(mat)
            
        except NotImplementedError:
            # It's v7.3, use h5py
            print("  Detected MATLAB v7.3, using h5py...")
            return self._load_mat_v73()
            
        except Exception as e:
            print(f"✗ Error loading .mat file: {e}")
            return False
    
    def _load_mat_v73(self):
        """
        Load MATLAB v7.3 files (HDF5 format)
        """
        try:
            import h5py
            
            with h5py.File(self.filepath, 'r') as f:
                # Find the data array
                data_found = False
                
                # Look for common field names
                common_names = ['data', 'EEG', 'eeg', 'signal', 'signals', 
                               'actualVariable', 'X', 'samples']
                
                for name in common_names:
                    if name in f:
                        dataset = f[name]
                        if isinstance(dataset, h5py.Dataset):
                            data = dataset[()]
                            
                            # Handle object references
                            if data.dtype.kind == 'O' and data.size == 1:
                                ref = data.item()
                                data = f[ref][()]
                            
                            data = np.array(data, dtype=np.float64)
                            
                            if data.ndim >= 2:
                                self.data = data
                                data_found = True
                                print(f"  ✓ Found data in field: '{name}'")
                                break
                
                if not data_found:
                    # Auto-detect: find largest 2D array
                    candidates = []
                    
                    def find_arrays(name, obj):
                        if isinstance(obj, h5py.Dataset) and len(obj.shape) == 2:
                            candidates.append((name, obj.shape, obj))
                    
                    f.visititems(find_arrays)
                    
                    if candidates:
                        # Use the one with most samples
                        name, shape, dataset = max(candidates, key=lambda x: max(x[1]))
                        self.data = dataset[()]
                        print(f"  ✓ Auto-detected data field: '{name}'")
                    else:
                        print("✗ Could not find EEG data in file")
                        return False
                
                # Look for sampling rate
                rate_found = False
                rate_names = ['srate', 'fs', 'Fs', 'sampling_rate', 'freq']
                
                for name in rate_names:
                    if name in f:
                        rate_data = f[name][()]
                        if rate_data.dtype.kind == 'O':
                            rate_data = f[rate_data.item()][()]
                        self.sampling_rate = float(rate_data)
                        rate_found = True
                        print(f"  ✓ Found sampling rate: {self.sampling_rate} Hz")
                        break
                
                if not rate_found:
                    self.sampling_rate = 250.0  # OpenBCI default
                    print(f"  ⚠ Using default sampling rate: {self.sampling_rate} Hz")
            
            # Ensure correct orientation (channels × samples)
            if self.data.shape[0] > self.data.shape[1]:
                print("  ℹ Transposing data (was samples × channels)")
                self.data = self.data.T
            
            self.n_channels = self.data.shape[0]
            self.channel_names = [f'CH{i+1}' for i in range(self.n_channels)]
            
            # Create MNE Raw object
            self._create_mne_raw()
            
            print("✓ MATLAB v7.3 file loaded successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error loading MATLAB v7.3 file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_from_scipy_mat(self, mat):
        """
        Extract data from scipy-loaded .mat file
        """
        # Remove MATLAB metadata
        mat = {k: v for k, v in mat.items() if not k.startswith('__')}
        
        # Find data field
        data_field = None
        common_names = ['data', 'EEG', 'eeg', 'signal', 'actualVariable']
        
        for name in common_names:
            if name in mat:
                data_field = name
                break
        
        if data_field is None:
            # Find largest 2D array
            for key, value in mat.items():
                if isinstance(value, np.ndarray) and value.ndim >= 2:
                    data_field = key
                    break
        
        if data_field is None:
            print("✗ Could not find data field")
            print(f"  Available fields: {list(mat.keys())}")
            return False
        
        data = mat[data_field]
        
        # Handle MATLAB structs
        if hasattr(data, '__dict__'):
            # Try to extract from struct
            for attr in ['data', 'EEG', 'eeg', 'signal']:
                if hasattr(data, attr):
                    data = getattr(data, attr)
                    break
        
        self.data = np.array(data)
        
        # Ensure 2D
        if self.data.ndim == 1:
            self.data = self.data.reshape(1, -1)
        
        # Ensure correct orientation
        if self.data.shape[0] > self.data.shape[1]:
            print("  ℹ Transposing data")
            self.data = self.data.T
        
        # Get sampling rate
        rate_names = ['srate', 'fs', 'Fs', 'sampling_rate']
        for name in rate_names:
            if name in mat:
                self.sampling_rate = float(mat[name])
                print(f"  ✓ Sampling rate: {self.sampling_rate} Hz")
                break
        
        if self.sampling_rate is None:
            self.sampling_rate = 250.0
            print(f"  ⚠ Using default sampling rate: {self.sampling_rate} Hz")
        
        self.n_channels = self.data.shape[0]
        self.channel_names = [f'CH{i+1}' for i in range(self.n_channels)]
        
        # Create MNE Raw object
        self._create_mne_raw()
        
        print(f"  ✓ Extracted from field: '{data_field}'")
        return True
    
    def _create_mne_raw(self):
        """
        Create MNE Raw object from data
        """
        info = mne.create_info(
            ch_names=self.channel_names,
            sfreq=self.sampling_rate,
            ch_types='eeg'
        )
        
        # Convert to volts (MNE standard)
        # Assume data is in microvolts
        data_volts = self.data * 1e-6
        
        self.raw = mne.io.RawArray(data_volts, info, verbose=False)
    
    def _extract_metadata(self):
        """
        Extract metadata from loaded Raw object
        """
        self.sampling_rate = self.raw.info['sfreq']
        self.n_channels = len(self.raw.ch_names)
        self.channel_names = self.raw.ch_names
        self.data = self.raw.get_data()
    
    def print_summary(self):
        """
        Print summary of loaded data
        """
        print(f"\n{'='*70}")
        print("DATA SUMMARY")
        print(f"{'='*70}")
        print(f"Sampling Rate: {self.sampling_rate} Hz")
        print(f"Channels: {self.n_channels}")
        print(f"Channel Names: {', '.join(self.channel_names[:8])}...")
        print(f"Duration: {self.raw.times[-1]:.2f} seconds")
        print(f"Total Samples: {len(self.raw.times):,}")
        print(f"Data Shape: {self.data.shape} (channels × samples)")
        print(f"{'='*70}\n")


def test_loader(filepath):
    """
    Test the loader on a file
    """
    loader = UniversalEEGLoader(filepath)
    
    if loader.load():
        loader.print_summary()
        return loader
    else:
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_loader(sys.argv[1])
    else:
        print("Usage: python3 universal_eeg_loader.py <path_to_eeg_file>")
        print("\nExample:")
        print("  python3 universal_eeg_loader.py dataset.mat")
        print("  python3 universal_eeg_loader.py dataset.edf")
