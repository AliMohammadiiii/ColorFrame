//! Error type carrying a schema error code (INPUT_OUTPUT_SCHEMA.md section 2).
use std::fmt;

pub const MALFORMED_INPUT: &str = "MALFORMED_INPUT";
pub const INVALID_ID: &str = "INVALID_ID";
pub const INVALID_DNA: &str = "INVALID_DNA";
pub const INVALID_COLORS: &str = "INVALID_COLORS";
pub const DUPLICATE_NODE: &str = "DUPLICATE_NODE";
pub const MISSING_NODE: &str = "MISSING_NODE";
pub const DUPLICATE_EDGE: &str = "DUPLICATE_EDGE";
pub const INVALID_OVERLAP: &str = "INVALID_OVERLAP";
pub const OVERLAP_MISMATCH: &str = "OVERLAP_MISMATCH";
pub const INCONSISTENT_OVERLAP: &str = "INCONSISTENT_OVERLAP";
pub const USAGE: &str = "USAGE";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CfError {
    pub code: &'static str,
    pub message: String,
}

impl CfError {
    pub fn new(code: &'static str, message: impl Into<String>) -> Self {
        CfError {
            code,
            message: message.into(),
        }
    }

    /// Process exit status: 64 for usage errors, 2 for validation errors.
    pub fn exit_status(&self) -> i32 {
        if self.code == USAGE {
            64
        } else {
            2
        }
    }
}

impl fmt::Display for CfError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "ERROR {}: {}", self.code, self.message)
    }
}

impl std::error::Error for CfError {}
