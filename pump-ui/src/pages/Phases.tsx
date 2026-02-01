import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Alert,
  Card,
  CardContent,
  CardHeader,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { pumpApi } from '../services/api';
import type { Phase, PhaseUpdateRequest, PhaseCreateRequest } from '../types/api';

interface EditingPhase extends Phase {
  isEditing: boolean;
  originalData: Phase;
}

interface NewPhaseForm {
  name: string;
  interval_seconds: number;
  min_age_minutes: number;
  max_age_minutes: number;
}

const Phases: React.FC = () => {
  const [phases, setPhases] = useState<EditingPhase[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>('');

  // Dialog States
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [phaseToDelete, setPhaseToDelete] = useState<EditingPhase | null>(null);
  const [newPhase, setNewPhase] = useState<NewPhaseForm>({
    name: '',
    interval_seconds: 15,
    min_age_minutes: 0,
    max_age_minutes: 60,
  });

  const fetchPhases = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await pumpApi.getPhases();
      setPhases(data.map((p: Phase) => ({
        ...p,
        isEditing: false,
        originalData: { ...p },
      })));
    } catch (err) {
      setError('Fehler beim Laden der Phasen');
      console.error('Error fetching phases:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPhases();
  }, []);

  const handleEdit = (phaseId: number) => {
    setPhases(prev => prev.map(p =>
      p.id === phaseId ? { ...p, isEditing: true } : p
    ));
  };

  const handleCancel = (phaseId: number) => {
    setPhases(prev => prev.map(p =>
      p.id === phaseId ? { ...p.originalData, isEditing: false, originalData: p.originalData } : p
    ));
  };

  const handleFieldChange = (phaseId: number, field: keyof Phase, value: string | number) => {
    setPhases(prev => prev.map(p =>
      p.id === phaseId ? { ...p, [field]: value } : p
    ));
  };

  const handleSave = async (phase: EditingPhase) => {
    setIsLoading(true);
    setError(null);

    // Validierung
    if (phase.interval_seconds < 1) {
      setError('Intervall muss mindestens 1 Sekunde sein');
      setIsLoading(false);
      return;
    }

    if (phase.max_age_minutes <= phase.min_age_minutes) {
      setError('Max Age muss größer als Min Age sein');
      setIsLoading(false);
      return;
    }

    try {
      const updateData: PhaseUpdateRequest = {};

      if (phase.name !== phase.originalData.name) {
        updateData.name = phase.name;
      }
      if (phase.interval_seconds !== phase.originalData.interval_seconds) {
        updateData.interval_seconds = phase.interval_seconds;
      }
      if (phase.min_age_minutes !== phase.originalData.min_age_minutes) {
        updateData.min_age_minutes = phase.min_age_minutes;
      }
      if (phase.max_age_minutes !== phase.originalData.max_age_minutes) {
        updateData.max_age_minutes = phase.max_age_minutes;
      }

      if (Object.keys(updateData).length === 0) {
        setSuccessMessage('Keine Änderungen erkannt');
        setTimeout(() => setSuccessMessage(''), 3000);
        setPhases(prev => prev.map(p =>
          p.id === phase.id ? { ...p, isEditing: false } : p
        ));
        setIsLoading(false);
        return;
      }

      const result = await pumpApi.updatePhase(phase.id, updateData);

      setSuccessMessage(`Phase "${result.phase.name}" aktualisiert. ${result.updated_streams} aktive Streams wurden angepasst.`);
      setTimeout(() => setSuccessMessage(''), 5000);

      // Refresh phases
      await fetchPhases();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Fehler beim Speichern der Phase';
      setError(errorMessage);
      console.error('Error updating phase:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // === ADD PHASE ===
  const handleOpenAddDialog = () => {
    // Finde die letzte reguläre Phase für sinnvolle Default-Werte
    const regularPhases = phases.filter(p => p.id < 99);
    const lastPhase = regularPhases[regularPhases.length - 1];

    setNewPhase({
      name: `Phase ${regularPhases.length + 1}`,
      interval_seconds: 15,
      min_age_minutes: lastPhase ? lastPhase.max_age_minutes : 0,
      max_age_minutes: lastPhase ? lastPhase.max_age_minutes + 60 : 60,
    });
    setAddDialogOpen(true);
  };

  const handleAddPhase = async () => {
    setIsLoading(true);
    setError(null);

    // Validierung
    if (!newPhase.name.trim()) {
      setError('Name darf nicht leer sein');
      setIsLoading(false);
      return;
    }

    if (newPhase.interval_seconds < 1) {
      setError('Intervall muss mindestens 1 Sekunde sein');
      setIsLoading(false);
      return;
    }

    if (newPhase.max_age_minutes <= newPhase.min_age_minutes) {
      setError('Max Age muss größer als Min Age sein');
      setIsLoading(false);
      return;
    }

    try {
      const createData: PhaseCreateRequest = {
        name: newPhase.name.trim(),
        interval_seconds: newPhase.interval_seconds,
        min_age_minutes: newPhase.min_age_minutes,
        max_age_minutes: newPhase.max_age_minutes,
      };

      const result = await pumpApi.createPhase(createData);

      setSuccessMessage(`Phase "${result.phase.name}" (ID: ${result.phase.id}) erfolgreich erstellt.`);
      setTimeout(() => setSuccessMessage(''), 5000);

      setAddDialogOpen(false);
      await fetchPhases();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Fehler beim Erstellen der Phase';
      setError(errorMessage);
      console.error('Error creating phase:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // === DELETE PHASE ===
  const handleOpenDeleteDialog = (phase: EditingPhase) => {
    setPhaseToDelete(phase);
    setDeleteDialogOpen(true);
  };

  const handleDeletePhase = async () => {
    if (!phaseToDelete) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await pumpApi.deletePhase(phaseToDelete.id);

      setSuccessMessage(result.message);
      setTimeout(() => setSuccessMessage(''), 5000);

      setDeleteDialogOpen(false);
      setPhaseToDelete(null);
      await fetchPhases();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Fehler beim Löschen der Phase';
      setError(errorMessage);
      console.error('Error deleting phase:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const isSystemPhase = (phaseId: number) => phaseId >= 99;

  const getPhaseColor = (phaseId: number): 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'default' => {
    if (phaseId === 99) return 'error';
    if (phaseId === 100) return 'secondary';
    if (phaseId === 1) return 'info';
    if (phaseId === 2) return 'warning';
    if (phaseId === 3) return 'success';
    return 'primary';
  };

  const regularPhaseCount = phases.filter(p => p.id < 99).length;
  const canDeletePhases = regularPhaseCount > 1;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h4">
          Tracking Phasen
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            color="success"
            startIcon={<AddIcon />}
            onClick={handleOpenAddDialog}
            disabled={isLoading}
          >
            Neue Phase
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchPhases}
            disabled={isLoading}
          >
            Aktualisieren
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage('')}>
          {successMessage}
        </Alert>
      )}

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Hinweis:</strong> Änderungen an Phasen wirken sich sofort auf alle aktiven Streams aus.
          System-Phasen (Finished, Graduated) können nicht bearbeitet oder gelöscht werden.
          Beim Löschen einer Phase werden betroffene Streams zur nächsten Phase verschoben.
        </Typography>
      </Alert>

      {isLoading && phases.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Card>
          <CardHeader
            title="Phasen-Konfiguration"
            subheader={`${regularPhaseCount} reguläre Phasen + 2 System-Phasen`}
          />
          <CardContent>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell width="60">ID</TableCell>
                    <TableCell width="180">Name</TableCell>
                    <TableCell width="120" align="right">Intervall (s)</TableCell>
                    <TableCell width="120" align="right">Min Age (min)</TableCell>
                    <TableCell width="120" align="right">Max Age (min)</TableCell>
                    <TableCell width="120" align="center">Aktionen</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {phases.map((phase) => (
                    <TableRow
                      key={phase.id}
                      sx={{
                        backgroundColor: phase.isEditing ? 'action.hover' : 'inherit',
                        opacity: isSystemPhase(phase.id) ? 0.7 : 1,
                      }}
                    >
                      <TableCell>
                        <Chip
                          label={phase.id}
                          size="small"
                          color={getPhaseColor(phase.id)}
                        />
                      </TableCell>
                      <TableCell>
                        {phase.isEditing ? (
                          <TextField
                            size="small"
                            value={phase.name}
                            onChange={(e) => handleFieldChange(phase.id, 'name', e.target.value)}
                            fullWidth
                          />
                        ) : (
                          <Typography variant="body2" fontWeight="medium">
                            {phase.name}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {phase.isEditing ? (
                          <TextField
                            size="small"
                            type="number"
                            value={phase.interval_seconds}
                            onChange={(e) => handleFieldChange(phase.id, 'interval_seconds', parseInt(e.target.value) || 1)}
                            inputProps={{ min: 1, max: 300 }}
                            sx={{ width: 80 }}
                          />
                        ) : (
                          <Typography variant="body2" fontFamily="monospace">
                            {phase.interval_seconds}s
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {phase.isEditing ? (
                          <TextField
                            size="small"
                            type="number"
                            value={phase.min_age_minutes}
                            onChange={(e) => handleFieldChange(phase.id, 'min_age_minutes', parseInt(e.target.value) || 0)}
                            inputProps={{ min: 0 }}
                            sx={{ width: 80 }}
                          />
                        ) : (
                          <Typography variant="body2" fontFamily="monospace">
                            {phase.min_age_minutes} min
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {phase.isEditing ? (
                          <TextField
                            size="small"
                            type="number"
                            value={phase.max_age_minutes}
                            onChange={(e) => handleFieldChange(phase.id, 'max_age_minutes', parseInt(e.target.value) || 1)}
                            inputProps={{ min: 1 }}
                            sx={{ width: 80 }}
                          />
                        ) : (
                          <Typography variant="body2" fontFamily="monospace">
                            {phase.max_age_minutes === 999999 ? '\u221E' : `${phase.max_age_minutes} min`}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {isSystemPhase(phase.id) ? (
                          <Tooltip title="System-Phase (nicht editierbar)">
                            <span>
                              <IconButton disabled size="small">
                                <WarningIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                        ) : phase.isEditing ? (
                          <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                            <Tooltip title="Speichern">
                              <IconButton
                                size="small"
                                color="primary"
                                onClick={() => handleSave(phase)}
                                disabled={isLoading}
                              >
                                <SaveIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Abbrechen">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleCancel(phase.id)}
                                disabled={isLoading}
                              >
                                <CancelIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        ) : (
                          <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                            <Tooltip title="Bearbeiten">
                              <IconButton
                                size="small"
                                onClick={() => handleEdit(phase.id)}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title={canDeletePhases ? "Löschen" : "Mindestens eine Phase erforderlich"}>
                              <span>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleOpenDeleteDialog(phase)}
                                  disabled={!canDeletePhases || isLoading}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                          </Box>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Phasen-Erklärung */}
      <Card sx={{ mt: 3 }}>
        <CardHeader
          title="Phasen-Erklärung"
          subheader="Was bedeuten die einzelnen Phasen?"
        />
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Reguläre Phasen bestimmen das Tracking-Intervall basierend auf dem Coin-Alter.
              Coins durchlaufen die Phasen automatisch, wenn sie die max_age_minutes einer Phase überschreiten.
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip label="99" color="error" size="small" />
              <Box>
                <Typography variant="body2" fontWeight="medium">Finished (System)</Typography>
                <Typography variant="caption" color="text.secondary">
                  Coins, deren Tracking beendet wurde (Bonding-Kurve voll oder Max-Age erreicht).
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip label="100" color="secondary" size="small" />
              <Box>
                <Typography variant="body2" fontWeight="medium">Graduated (System)</Typography>
                <Typography variant="caption" color="text.secondary">
                  Coins, die erfolgreich die Bonding-Kurve abgeschlossen haben.
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Add Phase Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Neue Phase erstellen</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Name"
              value={newPhase.name}
              onChange={(e) => setNewPhase(prev => ({ ...prev, name: e.target.value }))}
              fullWidth
              autoFocus
            />
            <TextField
              label="Intervall (Sekunden)"
              type="number"
              value={newPhase.interval_seconds}
              onChange={(e) => setNewPhase(prev => ({ ...prev, interval_seconds: parseInt(e.target.value) || 1 }))}
              inputProps={{ min: 1, max: 300 }}
              helperText="Wie oft Metriken gespeichert werden (1-300s)"
              fullWidth
            />
            <TextField
              label="Min Age (Minuten)"
              type="number"
              value={newPhase.min_age_minutes}
              onChange={(e) => setNewPhase(prev => ({ ...prev, min_age_minutes: parseInt(e.target.value) || 0 }))}
              inputProps={{ min: 0 }}
              helperText="Ab welchem Alter Coins diese Phase betreten"
              fullWidth
            />
            <TextField
              label="Max Age (Minuten)"
              type="number"
              value={newPhase.max_age_minutes}
              onChange={(e) => setNewPhase(prev => ({ ...prev, max_age_minutes: parseInt(e.target.value) || 1 }))}
              inputProps={{ min: 1 }}
              helperText="Bis zu welchem Alter Coins in dieser Phase bleiben"
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Abbrechen</Button>
          <Button onClick={handleAddPhase} variant="contained" color="success" disabled={isLoading}>
            Erstellen
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Phase Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Phase löschen?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Möchtest du die Phase <strong>"{phaseToDelete?.name}"</strong> (ID: {phaseToDelete?.id}) wirklich löschen?
            <br /><br />
            Aktive Streams in dieser Phase werden automatisch zur nächsten Phase verschoben.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Abbrechen</Button>
          <Button onClick={handleDeletePhase} variant="contained" color="error" disabled={isLoading}>
            Löschen
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Phases;
