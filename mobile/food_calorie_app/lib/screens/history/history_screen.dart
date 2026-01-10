import 'package:flutter/material.dart';
import 'package:food_calorie_app/generated/app_localizations.dart';
import '../../config/theme.dart';
import '../../models/prediction.dart';
import '../../services/history_service.dart';
import 'package:intl/intl.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final HistoryService _historyService = HistoryService();
  List<Prediction> _predictions = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await _historyService.getHistory(page: 1, limit: 50);

      if (mounted && result['success'] == true) {
        setState(() {
          _predictions = result['predictions'] as List<Prediction>;
          _isLoading = false;
        });
      } else {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.mealHistory),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () {
              // TODO: Show filter dialog
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _predictions.isEmpty
              ? _buildEmptyState()
              : _buildHistoryList(),
    );
  }

  Widget _buildEmptyState() {
    final l10n = AppLocalizations.of(context)!;

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.history,
            size: 100,
            color: Colors.grey.shade300,
          ),
          const SizedBox(height: 24),
          Text(
            l10n.emptyHistory,
            style: Theme.of(context).textTheme.displayMedium,
          ),
          const SizedBox(height: 8),
          Text(
            l10n.startTracking,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.of(context).pushNamed('/camera');
            },
            icon: const Icon(Icons.camera_alt),
            label: Text(l10n.scanFood),
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryList() {
    final groupedPredictions = _groupPredictionsByDate(_predictions);

    return ListView.builder(
      padding: const EdgeInsets.all(16.0),
      itemCount: groupedPredictions.length,
      itemBuilder: (context, index) {
        final date = groupedPredictions.keys.elementAt(index);
        final predictions = groupedPredictions[date]!;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8.0),
              child: Text(
                _formatDate(date),
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textSecondaryColor,
                    ),
              ),
            ),
            ...predictions.map((prediction) => _buildHistoryCard(prediction)),
            const SizedBox(height: 16),
          ],
        );
      },
    );
  }

  Map<DateTime, List<Prediction>> _groupPredictionsByDate(List<Prediction> predictions) {
    final Map<DateTime, List<Prediction>> grouped = {};

    for (final prediction in predictions) {
      if (prediction.createdAt == null) continue;

      final date = DateTime(
        prediction.createdAt!.year,
        prediction.createdAt!.month,
        prediction.createdAt!.day,
      );

      if (!grouped.containsKey(date)) {
        grouped[date] = [];
      }
      grouped[date]!.add(prediction);
    }

    return grouped;
  }

  String _formatDate(DateTime date) {
    final l10n = AppLocalizations.of(context)!;
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));

    if (date == today) {
      return l10n.today;
    } else if (date == yesterday) {
      return l10n.yesterday;
    } else {
      return DateFormat('EEEE, MMM d').format(date);
    }
  }

  Widget _buildHistoryCard(Prediction prediction) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12.0),
      child: InkWell(
        onTap: () {
          _openDetail(prediction);
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.restaurant,
                  color: AppTheme.primaryColor,
                  size: 32,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      prediction.foodClass,
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${prediction.estimatedGrams.toStringAsFixed(0)}g • ${prediction.createdAt != null ? DateFormat('HH:mm').format(prediction.createdAt!) : ''}',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${prediction.calories.toStringAsFixed(0)}',
                    style: Theme.of(context).textTheme.displayMedium?.copyWith(
                          color: AppTheme.accentColor,
                          fontSize: 20,
                        ),
                  ),
                  Text(
                    AppLocalizations.of(context)!.kcal,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _openDetail(Prediction prediction) async {
    final result = await Navigator.of(context).pushNamed('/history/detail', arguments: {'id': prediction.id});
    if (result == true) {
      _loadHistory();
    }
  }
}
