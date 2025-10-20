'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageCircle, CheckCircle, User } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

interface ProductQAProps {
  productId: string;
  vendorId?: string;
}

export function ProductQA({ productId, vendorId }: ProductQAProps) {
  const [showQuestionForm, setShowQuestionForm] = useState(false);
  const [questionText, setQuestionText] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [answeringQuestionId, setAnsweringQuestionId] = useState<string | null>(null);
  
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();

  const { data: qaData, isLoading } = useQuery({
    queryKey: ['qa', productId],
    queryFn: async () => {
      const response = await apiClient.getProductQA(productId);
      return response.data;
    },
  });

  const askQuestionMutation = useMutation({
    mutationFn: (question: string) =>
      apiClient.askQuestion({
        product: productId,
        question,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qa', productId] });
      toast.success('Question submitted successfully!');
      setQuestionText('');
      setShowQuestionForm(false);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to submit question';
      toast.error(errorMessage);
    },
  });

  const answerQuestionMutation = useMutation({
    mutationFn: ({ questionId, answer }: { questionId: string; answer: string }) =>
      apiClient.answerQuestion({
        question: questionId,
        answer,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qa', productId] });
      toast.success('Answer submitted successfully!');
      setAnswerText('');
      setAnsweringQuestionId(null);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to submit answer';
      toast.error(errorMessage);
    },
  });

  const handleAskQuestion = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      toast.error('Please login to ask a question');
      return;
    }
    if (questionText.trim().length < 10) {
      toast.error('Question must be at least 10 characters');
      return;
    }
    askQuestionMutation.mutate(questionText.trim());
  };

  const handleSubmitAnswer = (e: React.FormEvent, questionId: string) => {
    e.preventDefault();
    if (!isAuthenticated) {
      toast.error('Please login to answer questions');
      return;
    }
    if (answerText.trim().length < 5) {
      toast.error('Answer must be at least 5 characters');
      return;
    }
    answerQuestionMutation.mutate({ questionId, answer: answerText.trim() });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-32 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  const questions = Array.isArray(qaData) ? qaData : qaData?.results || [];
  const totalQuestions = questions.length;

  return (
    <div className="space-y-6">
      {/* Q&A Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Questions & Answers</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {totalQuestions} {totalQuestions === 1 ? 'question' : 'questions'}
          </p>
        </div>
        {isAuthenticated && (
          <Button onClick={() => setShowQuestionForm(!showQuestionForm)}>
            {showQuestionForm ? 'Cancel' : 'Ask a Question'}
          </Button>
        )}
      </div>

      {/* Question Form */}
      {showQuestionForm && (
        <Card>
          <CardHeader>
            <CardTitle>Ask Your Question</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAskQuestion} className="space-y-4">
              <textarea
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                placeholder="What would you like to know about this product?"
                className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                required
              />
              <p className="text-xs text-muted-foreground">
                {questionText.length} characters (minimum 10)
              </p>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={askQuestionMutation.isPending}
                >
                  {askQuestionMutation.isPending ? 'Submitting...' : 'Submit Question'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowQuestionForm(false);
                    setQuestionText('');
                  }}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Questions List */}
      {totalQuestions === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <MessageCircle className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-4 text-muted-foreground">
              No questions yet. Be the first to ask!
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {questions.map((question: any) => (
            <Card key={question.id}>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  {/* Question */}
                  <div className="flex gap-4">
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-muted">
                      <User className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">
                          {question.user?.username || 'Anonymous'}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          asked {format(new Date(question.created_at), 'MMM d, yyyy')}
                        </span>
                      </div>
                      <p className="text-sm leading-relaxed">{question.question}</p>
                    </div>
                  </div>

                  {/* Answers */}
                  {question.answers && question.answers.length > 0 ? (
                    <div className="ml-14 space-y-3 border-l-2 border-muted pl-6">
                      {question.answers.map((answer: any) => (
                        <div key={answer.id} className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">
                              {answer.user?.username || 'Anonymous'}
                            </span>
                            {answer.is_vendor && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">
                                <CheckCircle className="h-3 w-3" />
                                Vendor
                              </span>
                            )}
                            <span className="text-sm text-muted-foreground">
                              answered {format(new Date(answer.created_at), 'MMM d, yyyy')}
                            </span>
                          </div>
                          <p className="text-sm leading-relaxed text-muted-foreground">
                            {answer.answer}
                          </p>
                          {answer.helpful_votes > 0 && (
                            <p className="text-xs text-muted-foreground">
                              {answer.helpful_votes} {answer.helpful_votes === 1 ? 'person' : 'people'} found this helpful
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="ml-14 text-sm text-muted-foreground">No answers yet</p>
                  )}

                  {/* Answer Form */}
                  {isAuthenticated && answeringQuestionId === question.id ? (
                    <div className="ml-14 border-l-2 border-muted pl-6">
                      <form
                        onSubmit={(e) => handleSubmitAnswer(e, question.id)}
                        className="space-y-3"
                      >
                        <textarea
                          value={answerText}
                          onChange={(e) => setAnswerText(e.target.value)}
                          placeholder="Your answer..."
                          className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          required
                        />
                        <div className="flex gap-2">
                          <Button
                            type="submit"
                            size="sm"
                            disabled={answerQuestionMutation.isPending}
                          >
                            {answerQuestionMutation.isPending ? 'Submitting...' : 'Submit Answer'}
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setAnsweringQuestionId(null);
                              setAnswerText('');
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </form>
                    </div>
                  ) : (
                    isAuthenticated &&
                    (!question.answers || question.answers.length === 0) && (
                      <div className="ml-14">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setAnsweringQuestionId(question.id)}
                        >
                          Answer this question
                        </Button>
                      </div>
                    )
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

